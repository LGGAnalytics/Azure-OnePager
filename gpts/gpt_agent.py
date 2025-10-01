import os, textwrap
import io

from typing import List, Dict, Optional
from xml.sax.saxutils import escape

from gpts.gpt_assistants import general_assistant
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

from prompts4 import finance_calculations
import re 
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
OPENAI_API_KEY  = os.getenv("OPENAI_API_KEY")        # required

# ------------------ CODE

class profileAgent():

    """Hybrid (dense+sparse) RAG over Vector Store

    This Agent is responsible for creating Company Profiles. 
    It operates with gpt5.
    It is activated by a call on main rag when it is typed 'Create company profile'
    """

    def __init__(self, company_name, k, max_text_recall_size, max_chars, model, profile_prompt = new_system_finance_prompt, finance_calculations = finance_calculations):
        self.company_name = company_name

        self.k = k
        self.max_text_recall_size = max_text_recall_size
        self.model = model
        self.max_chars = max_chars

        self.azure_credentials = AzureKeyCredential(SEARCH_KEY) if SEARCH_KEY else DefaultAzureCredential()
        self.search_client = SearchClient(SEARCH_ENDPOINT, SEARCH_INDEX, credential=self.azure_credentials)

        self.az_openai = AzureOpenAI(azure_endpoint=AOAI_ENDPOINT, api_key=AOAI_KEY, api_version=AOAI_API_VER)
        self.profile_prompt = profile_prompt

        self.finance_calculations = finance_calculations
    def _company_filter(self) -> str:
        v = (self.company_name or "").replace("'", "''").strip()
        return f"company_name eq '{v}'" if v else None
    
    def assemble_bm25_from_llm(self, slots: dict) -> str:
        def q(s: str) -> str:
            # sanitize: remove internal quotes and trim
            s = (s or "").strip().replace('"', ' ')
            return f"\"{s}\"" if s else ""
        groups = []

        # must-have phrases (ANDed)
        for p in slots.get("must_have_phrases", []):
            qp = q(p)
            if qp:
                groups.append(qp)

        # metric / statement synonym groups (ORed within each group)
        for key in ["metric", "statement"]:
            syns = slots.get("synonyms", {}).get(key, []) or slots.get(key, [])
            syns = [q(s) for s in syns if s]
            if syns:
                groups.append("(" + " OR ".join(syns) + ")")

        return " AND ".join(groups) if groups else "\"financial statements\""


    def bm25_creator(self, prompt):

        instruction = (
            "Extract finance search slots for Azure AI Search. "
            "Return strict JSON: {\"metric\":[], \"statement\":[], \"synonyms\":{}, \"must_have_phrases\":[]} "
            "(include IFRS/US GAAP variants)."
        )
        resp = general_assistant(instruction, prompt, OPENAI_API_KEY, 'gpt-4o')

        try:
            slots = getattr(resp, "output_json", None)
            if slots is None:
                import json
                slots = json.loads(resp.output_text)
        except Exception:
            # fallback: minimal anchors from prompt
            slots = {"must_have_phrases": [prompt], "metric": [], "statement": [], "synonyms": {}}
        return self.assemble_bm25_from_llm(slots)

    def _retrieve_hybrid_enhanced(self, query_nl, k: int = 50, top_n = 30, fields=VECTOR_FIELD, max_text_recall_size:int = 800):
        sc = self.search_client
        flt = self._company_filter()
        
        try:
            vq = VectorizableTextQuery(text=query_nl, k=k, fields=VECTOR_FIELD)
            # Prefer vector-only search (integrated vectorization). If your index isn't set up for it, this raises.
            results = sc.search(
                search_text=self.bm25_creator(query_nl), 
                vector_queries=[vq], 
                top=top_n, 
                query_type="semantic",
                query_caption="extractive", 
                hybrid_search=HybridSearch(max_text_recall_size=self.max_text_recall_size),
                query_caption_highlight_enabled=True,
                filter=flt
                )
            mode = "hybrid + semantic"
        except HttpResponseError as e:
            # Fall back to lexical so you still get results while fixing vector config
            results = sc.search(search_text=self.bm25_creator(query_nl), top=k)
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


    def _build_context(self, hits: List[Dict], text_field: str = TEXT_FIELD, max_chars: int = 20000):
        """Build a compact, numbered context block and also return the selected chunk metadata."""
        lines = []
        total = 0
        selected = []  # <- we'll return this

        for i, h in enumerate(hits, 1):
            title     = h.get("title")
            chunk_id  = h.get("chunk_id")
            full_text = (h.get(text_field) or "")
            if not full_text:
                continue

            preview = textwrap.shorten(full_text, width=700, placeholder=" ...")
            block = f"[{i}] title={title!r} | chunk_id={chunk_id} | score={h.get('score'):.4f}\n{full_text}"

            if total + len(block) > self.max_chars:
                break

            total += len(block)
            lines.append(block)

            # keep rich metadata so you can show or log it later
            selected.append({
                "i": i,
                "title": title,
                "chunk_id": chunk_id,
                "score": h.get("score"),
                "caption": h.get("caption"),
                "preview": preview,
                "text": full_text,  # full chunk text (not shortened)
                # include any other fields you index, if available:
                "metadata_storage_path": h.get("metadata_storage_path"),
                "page_number": h.get("page_number"),
                "doc_type": h.get("doc_type"),
            })

        return "\n\n---\n\n".join(lines), selected

        
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
    
    def _extract_cited_idxs(self, answer: str) -> list[int]:
        # Matches [#1], [#12], etc. (also tolerates stray [1])
        nums = set(int(n) for n in re.findall(r"\[#?(\d+)\]", answer))
        return sorted(nums)

    def _rag_answer(self, rag_nl, question, k: int = 5, temperature: float = 0.2):


        # question = f'CREATE A SECTION OF COMPANY PROFILE USING LAST YEARS OF ANNUAL REPORT PRESENT IN THE CONTEXT FOR {self.company_name}. IF ANY INFORMATION IS NOT FOUND STATE AS n.a. .\n\n THIS IS THE SECTION TO BE BUILT: \n {section7}  \n USE THIS TO GUIDE YOURSELF ON SEMANTIC TERMS AND HOW TO CALCULATE: \n {finance_calculations}'
        
        mode, hits = self._retrieve_hybrid_enhanced(
            # query=rag_q, 
            query_nl=rag_nl,
            k=25
            )
        ctx_text, ctx_items = self._build_context(hits)

        system_msg = self.profile_prompt + (
            "\nWhen you use a fact from the context, add citations like [#1], [#2]."
            "\nOnly rely on the numbered context; if a value is missing, say 'n.a.'."
        )
        user_msg = f"Question:\n{question}\n\nContext snippets (numbered):\n{ctx_text}"

        client = self.az_openai
        messages = [
            {"role": "system", "content": system_msg},
            {"role": "user",   "content": user_msg},
        ]

        # Try streaming first (SSE). Some networks/proxies block streaming; if so, fall back.
        
        resp = client.chat.completions.create(
            model=AOAI_DEPLOYMENT,
            messages=messages,
            reasoning_effort="high"
        )
        answer = resp.choices[0].message.content
        mode_model = "non-streaming (fallback)"

        cited = self._extract_cited_idxs(answer)
        used_chunks = [c for c in ctx_items if c["i"] in cited]

        # return self._generate_pdf(answer)
        return {
            "answer": answer,
            "citations": cited,          # [1, 3, 7]
            "used_chunks": used_chunks,  # detailed dicts for each cited snippet
            "all_chunks": ctx_items,     # everything you sent (optional)
            "mode": mode                 # retrieval mode info (optional)
        }