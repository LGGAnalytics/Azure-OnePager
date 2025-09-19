import os, textwrap
import io

from typing import List, Dict, Optional
from xml.sax.saxutils import escape

from dotenv import load_dotenv, find_dotenv
from azure.identity import DefaultAzureCredential
from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient
from azure.search.documents.models import VectorizableTextQuery
from azure.core.exceptions import HttpResponseError
from azure.search.documents.models import HybridSearch

from openai import AzureOpenAI, APIConnectionError
from prompts import new_system_finance_prompt

from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer

load_dotenv(find_dotenv(), override=True)

# ---- Config (expects the same envs you already used) ----
SEARCH_ENDPOINT = os.environ["AZURE_SEARCH_ENDPOINT"]
SEARCH_INDEX    = os.environ["AZURE_SEARCH_INDEX"]
SEARCH_KEY      = os.getenv("AZURE_SEARCH_API_KEY")  # omit if using AAD/RBAC
VECTOR_FIELD    = os.getenv("VECTOR_FIELD")
TEXT_FIELD      = os.getenv("TEXT_FIELD")

AOAI_ENDPOINT   = os.environ["AZURE_OPENAI_ENDPOINT"]            # https://<resource>.openai.azure.com
AOAI_API_VER    = os.environ.get("AZURE_OPENAI_API_VERSION", "2024-10-21")
AOAI_DEPLOYMENT = os.environ["AZURE_OPENAI_DEPLOYMENT"]          # e.g., gpt-4o-mini / o3-mini / gpt-5 preview
AOAI_KEY        = os.getenv("AZURE_OPENAI_API_KEY")              # omit if using AAD

# ------------------ CODE

class profileAgent():

    """Hybrid (dense+sparse) RAG over Vector Store

    This Agent is responsible for creating Company Profiles. 
    It operates with gpt5.
    It is activated by a call on main rag when it is typed 'Create company profile'
    """

    def __init__(self, company_name, k, max_text_recall_size, max_chars, model, profile_prompt = new_system_finance_prompt):
        self.company_name = company_name

        self.k = k
        self.max_text_recall_size = max_text_recall_size
        self.model = model
        self.max_chars = max_chars

        self.azure_credentials = AzureKeyCredential(SEARCH_KEY) if SEARCH_KEY else DefaultAzureCredential()
        self.search_client = SearchClient(SEARCH_ENDPOINT, SEARCH_INDEX, credential=self.azure_credentials)

        self.az_openai = AzureOpenAI(azure_endpoint=AOAI_ENDPOINT, api_key=AOAI_KEY, api_version=AOAI_API_VER)
        self.profile_prompt = profile_prompt

    def _retrieve_hybrid_enhanced(self, query: str, k: int = 10, fields=VECTOR_FIELD, max_text_recall_size:int = 200):
        sc = self.search_client
        try:
            vq = VectorizableTextQuery(text=query, k=k, fields=VECTOR_FIELD)
            # Prefer vector-only search (integrated vectorization). If your index isn't set up for it, this raises.
            results = sc.search(
                search_text=query, 
                vector_queries=[vq], 
                top=self.k, 
                query_type="semantic",
                query_caption="extractive", 
                hybrid_search=HybridSearch(max_text_recall_size=self.max_text_recall_size),
                query_caption_highlight_enabled=True,
                )
            mode = "hybrid + semantic"
        except HttpResponseError as e:
            # Fall back to lexical so you still get results while fixing vector config
            results = sc.search(search_text=query, top=k)
            mode = f"lexical (fallback due to: {e.__class__.__name__})"

        hits: List[Dict] = []
        for r in results:
            d = r.copy() if hasattr(r, "copy") else {k2: r[k2] for k2 in r}
            d["score"] = d.get("@search.reranker_score") or d.get("@search.score") or 0.0
            caps = d.get("@search.captions")
            if isinstance(caps, list) and caps:
                d["caption"] = getattr(caps[0], "text", None)
            hits.append(d)

        return mode, hits


    def _build_context(self, hits: List[Dict], text_field: str = TEXT_FIELD, max_chars: int = 20000) -> str:
        """Build a compact, numbered context block to feed the model."""
        lines = []
        total = 0
        for i, h in enumerate(hits, 1):
            title     = h.get("title")
            chunk_id  = h.get("chunk_id")
            snippet   = (h.get(text_field) or "")
            if not snippet:
                continue
            snippet = textwrap.shorten(snippet, width=700, placeholder=" ...")
            block = f"[{i}] title={title!r} | chunk_id={chunk_id} | score={h.get('score'):.4f}\n{snippet}"
            if total + len(block) > self.max_chars:
                break
            total += len(block)
            lines.append(block)
        return "\n\n---\n\n".join(lines)
    
    def _generate_pdf(self, text: str) -> bytes:

        buf = io.BytesIO()
        doc = SimpleDocTemplate(buf, pagesize=letter)
        styles = getSampleStyleSheet()
        body = styles["BodyText"]

        story = []
        # Treat double newlines as paragraph breaks; keep single newlines as <br/>
        for para in (text or "").split("\n\n"):
            safe = escape(para).replace("\n", "<br/>")
            story.append(Paragraph(safe if safe.strip() else "&nbsp;", body))
            story.append(Spacer(1, 8))

        doc.build(story)
        buf.seek(0)
        return buf.getvalue()

    def _rag_answer(self, k: int = 5, temperature: float = 0.2):
        question = f'Create the company profile of {self.company_name}. USE ONLY the information from latest annual report.'

        mode, hits = self._retrieve_hybrid_enhanced(
            query=question, 
            k=k
            )
        ctx = self._build_context(hits)

        system_msg = (
            self.profile_prompt
        )
        user_msg = f"Question:\n{question}\n\nContext snippets (numbered):\n{ctx}"

        client = self.az_openai
        messages = [
            {"role": "system", "content": system_msg},
            {"role": "user",   "content": user_msg},
        ]

        # Try streaming first (SSE). Some networks/proxies block streaming; if so, fall back.
        
        resp = client.chat.completions.create(
            model=AOAI_DEPLOYMENT,
            messages=messages,
        )
        answer = resp.choices[0].message.content
        mode_model = "non-streaming (fallback)"

        return self._generate_pdf(answer)