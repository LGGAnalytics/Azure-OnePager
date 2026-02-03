import os, textwrap
import io
import re, time

from typing import List, Dict, Optional
from xml.sax.saxutils import escape

from models.agents.agent_assistants import general_assistant
from dotenv import load_dotenv, find_dotenv

from openai import AzureOpenAI, APIConnectionError, OpenAI
from scripts.default_prompts import new_system_finance_prompt

from scripts.section_prompts import finance_pairs, finance_commentary_pairs, capital_pairs, capital_commentary_pairs, stakeholders_pairs, biz_overview_pairs, revenue_pairs, section4a, section4b, section5, biz_overview_web, stakeholders_web
from scripts.section_formatting import system_mod, finance_calculations, default_gpt_prompt, section3
from utils.formatting_tools import *

from scripts.section_formatting import *
import asyncio
from xml.sax.saxutils import escape

# TEACHING NOTE: Import async versions of clients
from openai import AsyncOpenAI, AsyncAzureOpenAI,APIConnectionError  # ← Async version!
# from azure.openai import AsyncAzureOpenAI  # ← Async version! (uncomment when available)

# For Azure Search - check if async version exists
from azure.search.documents.aio import SearchClient
from azure.identity.aio import DefaultAzureCredential

from azure.search.documents.models import VectorizableTextQuery, HybridSearch
from azure.core.credentials import AzureKeyCredential
from azure.core.exceptions import HttpResponseError

from langfuse import observe
from langsmith import traceable
from langfuse import get_client
from langsmith import run_helpers
from langsmith import wrappers

import logging
import sys

langfuse = get_client()

# Configure logging to display in Jupyter
logging.basicConfig(
    level=logging.INFO,  # Set to DEBUG for more verbose output
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)  # Print to stdout (Jupyter cell output)
    ]
)

# Get logger for your module
logger = logging.getLogger(__name__)
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
OPENAI_REASONING_MODEL = os.getenv("AZURE_OPENAI_DEPLOYMENT_ENHANCED", "gpt-5.2")  # Enhanced reasoning model
AOAI_KEY        = os.getenv("AZURE_OPENAI_API_KEY")              # omit if using AAD
OPENAI_API_KEY  = os.getenv("OPENAI_API_KEY")        # required

@traceable(run_type="llm", name="General Assistant")
@observe(as_type="generation", name="General Assistant")
async def async_general_assistant_async(prompt_sys, prompt_user, OPENAI_API_KEY, deployment, reasoning_effort = "medium"):
    """
    Async version: Designed to receive two text inputs and create a 
    summary out of them in order to join both prompts into one
    """    
    web_openai = AsyncOpenAI(api_key=OPENAI_API_KEY)

    REASONING_MODELS = {
        "o3", "o3-mini", "o3-mini-high", "o4-mini", 'gpt-5'
    }

    NON_REASONING_MODELS = {
        "gpt-4o", "gpt-4.1", "gpt-4.1-mini",
    }   

    if deployment in NON_REASONING_MODELS:
        try:
            resp = await web_openai.responses.create(
                model=deployment,
                input=[
                    {"role": "system",
                    "content": f"""
                        {prompt_sys}
                    """},
                    {"role": "user", 
                    "content": f"""Input: \n {prompt_user}
                    """},
                ]
            )
        except APIConnectionError:
            return False
    elif deployment in REASONING_MODELS:
        try:
            resp = await web_openai.responses.create(
                model=deployment,
                input=[
                    {"role": "system",
                    "content": f"""
                        {prompt_sys}
                    """},
                    {"role": "user", 
                    "content": f"""Input: \n {prompt_user}
                    """},
                ],
                reasoning={"effort": reasoning_effort}
            )
        except APIConnectionError:
            return False

        # ===================== MONITORING BLOCK
        usage = resp.usage
        # langfuse.update_current_trace(
        #     usage={
        #         "input": usage.prompt_tokens,
        #         "output": usage.completion_tokens,
        #         "total": usage.total_tokens
        #     },
        #     model=AOAI_DEPLOYMENT # Ensure this matches the Model Settings name
        # )

        run_tree = run_helpers.get_current_run_tree()
        if run_tree:
            run_tree.add_metadata({
                "token_usage": {
                    "prompt_tokens": usage.prompt_tokens,
                    "completion_tokens": usage.completion_tokens,
                    "total_tokens": usage.total_tokens
                }
            })
        # ===================== MONITORING BLOCK
            
    return resp.output_text




class AsyncProfileAgent:
    """
    1st Asnyc version of profileAgent
    """

    def __init__(self, company_name, k, max_text_recall_size, max_chars, model, profile_prompt="default_prompt", finance_calculations=finance_calculations, enable_faithfulness_eval = False, faithfulness_threshold = 0.7):

        self.company_name = company_name
        self.k = k
        self.max_text_recall_size = max_text_recall_size
        self.max_chars = max_chars
        
        self.azure_credentials = AzureKeyCredential(SEARCH_KEY)  # Replace with actual
        # NOTE: search_client is now created per-request for thread safety in async context
        # See _retrieve_hybrid_enhanced for isolated client creation
        self.az_openai = AsyncAzureOpenAI(
            azure_endpoint=AOAI_ENDPOINT,
            api_key=AOAI_KEY,
            api_version=AOAI_API_VER
        )
        self.openai = wrappers.wrap_openai(AsyncOpenAI(api_key=OPENAI_API_KEY))

        self.profile_prompt = profile_prompt
        self.reasoning_effort = "medium"
        self.verbosity = "medium"
        self.finance_calculations = finance_calculations

        # Limitation on concurrency - lazy initialization
        self._semaphore = None

        self.final_text = ""

        # Evaluation metrics
        self.enable_faithfulness_eval = enable_faithfulness_eval
        if enable_faithfulness_eval:
            from tests.deepeval_evaluators import RAGFaithfulnessEvaluator, SynthesisFaithfulnessEvaluator
            self.rag_evaluator = RAGFaithfulnessEvaluator(
                model="gpt-4o",
                threshold=faithfulness_threshold
            )
            self.synthesis_evaluator = SynthesisFaithfulnessEvaluator(
                model="gpt-4o",
                threshold=faithfulness_threshold
            )
            self.evaluation_results = []  # Store all evaluations


    # =================== HELPER FUNCTIONS ============
    @property
    def semaphore(self):
        """Lazy initialization of semaphore in async context"""
        if self._semaphore is None:
            self._semaphore = asyncio.Semaphore(3)
        return self._semaphore

    @traceable(run_type="chain", name="Filter company name")
    @observe(as_type="span", name="Filter company name")
    def _company_filter(self) -> str:
        """String manipulation"""
        v = (self.company_name or "").replace("'","''").strip()
        return f"company_name eq '{v}'"if v else None
    
    @traceable(run_type="chain", name="Assemble BM25 Query")
    @observe(as_type="span", name="Assemble BM25 Query")
    def assemble_bm25_from_llm(self, slots:dict) -> str:
        """String manipulation"""

        def q(s: str) -> str:
            s = (s or "").strip().replace('"',' ')
            return f"\"{s}\""if s else ""
        
        groups = []
        for p in slots.get("must_have_phrases",[]):
            qp = q(p)
            if qp:
                groups.append(qp)

        for key in ['metric','statemenet']:
            syns = slots.get("synonyms",{}).get(key, []) or slots.get(key, [])
            syns = [q(s) for s in syns if s]
            if syns:
                groups.append("("+ " OR ".join(syns) + ")")

        return " AND ".join(groups) if groups else "\"financial statements\""
    
    @traceable(run_type="chain", name="Build Context")
    @observe(as_type="span", name="Build Context")
    def _build_context(self, hits: List[Dict], text_field: str = TEXT_FIELD, max_chars: int = 20000):
        """
        Data processing
        """
        lines = []
        total = 0
        selected = []

        for i, h in enumerate(hits, 1):
            title = h.get("title")
            chunk_id = h.get("chunk_id")
            full_text = (h.get(text_field) or "")
            if not full_text:
                continue

            preview = textwrap.shorten(full_text, width=700, placeholder=" ...")
            block = f"[{i}] title={title!r} | chunk_id={chunk_id} | score={h.get('score'):.4f}\n{full_text}"

            if total + len(block) > self.max_chars:
                break

            total += len(block)
            lines.append(block)

            selected.append({
                "i": i,
                "title": title,
                "chunk_id": chunk_id,
                "score": h.get("score"),
                "caption": h.get("caption"),
                "preview": preview,
                "text": full_text,
                "metadata_storage_path": h.get("metadata_storage_path"),
                "page_number": h.get("page_number"),
                "doc_type": h.get("doc_type"),
            })

        return "\n\n---\n\n".join(lines), selected
    

    def _extract_cited_idxs(self, answer: str) -> list[int]:
        """Simple regex - stays synchronous"""
        nums = set(int(n) for n in re.findall(r"\[#?(\d+)\]", answer))
        return sorted(nums)

    @staticmethod
    def has_na(text: str) -> bool:
        """Simple regex check - stays synchronous"""
        return bool(re.search(r"\b(n\.a\.|n/a)\b", text, flags=re.I))

    # ======================== ASYNC METHODS

    @traceable(run_type="chain", name="Query Expansion")
    @observe(as_type="generation", name="Query Expansion")
    async def bm25_creator(self, prompt):

        """
        It makes an API to create the bm25 ideal prompt out of a prompt
        """
        instruction = (
            "Extract finance search slots for Azure AI Search. "
            "Return strict JSON: {\"metric\":[], \"statement\":[], \"synonyms\":{}, \"must_have_phrases\":[]} "
            "(include IFRS/US GAAP variants)."
        )

        # resp = await self.az_openai.chat.completions.create(
        #     model='gpt-4o',
        #     messages=[
        #         {"role": "system", "content": instruction},
        #         {"role": "user", "content": prompt}
        #     ]
        # )

        resp = await async_general_assistant_async(instruction, prompt, OPENAI_API_KEY, 'gpt-4o')

        try:
            import json
            slots = json.loads(resp.choices[0].message.content)
        except Exception:
            slots = {"must_have_phrases": [prompt], "metric": [], "statement": [], "synonyms": {}}

        return self.assemble_bm25_from_llm(slots)
    
    @traceable(run_type="retriever", name="Azure Hybrid Search")
    @observe(as_type="retriever", name="Azure Hybrid Search")
    async def _retrieve_hybrid_enhanced(self, query_nl, k: int = 50, top_n = 20, fields=VECTOR_FIELD, max_text_recall_size: int = 800):
        """
        search operation that mixes bm25 quey with vector search

        IMPORTANT: Creates an isolated SearchClient per request to prevent
        race conditions when multiple sections query in parallel.
        """

        # Create isolated search client for THIS request only
        # This prevents concurrent searches from interfering with each other
        from azure.search.documents.aio import SearchClient as AsyncSearchClient

        sc = AsyncSearchClient(
            endpoint=SEARCH_ENDPOINT,
            index_name=SEARCH_INDEX,
            credential=self.azure_credentials
        )

        flt = self._company_filter()
        bm25_query = await self.bm25_creator(query_nl)

        try:
            vq = VectorizableTextQuery(text=query_nl, k=k, fields=fields)

            results = await sc.search(
                search_text=bm25_query,
                vector_queries=[vq],
                top=top_n,
                query_type="semantic",
                query_caption="extractive",
                hybrid_search=HybridSearch(max_text_recall_size=max_text_recall_size),
                query_caption_highlight_enabled=True,
                filter=flt
            )
            mode = "hybrid + semantic"
        except HttpResponseError as e:
            results = await sc.search(search_Text=bm25_query, top=k)
            mode = f"lexical fallback due to: {e.__class__.__name__})"

        hits: List[Dict] = []

        # Eagerly consume the async iterator to avoid state corruption
        results_list = [r async for r in results]

        # Close the isolated search client to free resources
        await sc.close()

        for r in results_list:  # ← Regular for loop
            d = r.copy() if hasattr(r, "copy") else {k2: r[k2] for k2 in r}
            d["score"] = d.get("@search.reranker_score") or d.get("@search.scorre") or 0.0
            caps = d.get("@search.captions")
            if isinstance(caps, list) and caps:
                d["caption"] = getattr(caps[0], "text", None)
            hits.append(d)

        return mode, hits
    
    @traceable(run_type="chain", name="RAG Answer")
    @observe(as_type="generation")
    async def _rag_answer(self, rag_nl, question, k = 5, temperature = 0.2, calculations = None):
        """
        
        Calls multiple async chains to answer questions in different workflows

        """

        async with self.semaphore:

            mode, hits = await self._retrieve_hybrid_enhanced(
                query_nl=rag_nl,
                k=25
            )
            logging.info(f"🔍 Retrieved {len(hits)} hits")

            ctx_text, ctx_items = self._build_context(hits)
            # logging.info(f"📄 Context length: {len(ctx_text)} chars")
            # logging.info(f"📋 Context items: {len(ctx_items)}")

            # if not ctx_text:
            #     logging.error("❌ Context is EMPTY!")
                
            if calculations is None:
                system_msg = self.profile_prompt + (
                    "\nWhen you use a fact from the context, add citations like [#1], [#2]."
                    "\nOnly rely on the numbered context; if a value is missing, say 'n.a.'."
                    "\nIF ANY INFORMATION IS NOT FOUND STATE AS n.a."
                )
            else:
                system_msg = self.profile_prompt + "\n" + calculations + (
                    "\nWhen you use a fact from the context, add citations like [#1], [#2]."
                    "\nOnly rely on the numbered context; if a value is missing, say 'n.a.'."
                    "\nIF ANY INFORMATION IS NOT FOUND STATE AS n.a."
                    f"\n=========CALCULATIONS INSTRUCTIONS=========\n {calculations}"
                )

            user_msg = f"Question: \n{question}\n\n Context snippers (numbered): \n{ctx_text}"

            client = self.openai
            messages = [
                {"role":"system", "content": system_msg},
                {"role":"user","content": user_msg},
            ]

            # async api call

            resp = await client.chat.completions.create(
                model = AOAI_DEPLOYMENT,
                messages = messages,
                # temperature = temperature,
                # reasoning_effort = "high"
            )

            # ===================== MONITORING BLOCK
            usage = resp.usage
            # langfuse.update_current_trace(
            #     usage={
            #         "input": usage.prompt_tokens,
            #         "output": usage.completion_tokens,
            #         "total": usage.total_tokens
            #     },
            #     model=AOAI_DEPLOYMENT # Ensure this matches the Model Settings name
            # )
            run_tree = run_helpers.get_current_run_tree()
            if run_tree:
                run_tree.add_metadata({
                    "token_usage": {
                        "prompt_tokens": usage.prompt_tokens,
                        "completion_tokens": usage.completion_tokens,
                        "total_tokens": usage.total_tokens
                    }
                })
            # ===================== MONITORING BLOCK
            
            answer = resp.choices[0].message.content
            cited = self._extract_cited_idxs(answer)
            used_chunks = [c for c in ctx_items if c["i"] in cited]

            result = {
                "answer": answer,
                "citations": cited,
                "used_chunks": used_chunks,
                "all_chunks": ctx_items,
                "mode": mode
            }

            # ============== EVALUATION BLOCK

            if self.enable_faithfulness_eval:
                eval_result = await self.rag_evaluator.evaluate_rag_answer(
                    question=question,
                    answer=answer,
                    retrieval_context=ctx_text,
                    citations=cited,
                    all_chunks=ctx_items
                )
                result["faithfulness_eval"] = eval_result
                self.evaluation_results.append({
                    "type": "rag_answer",
                    "question": question,
                    "eval": eval_result
                })
                
                # Log evaluation result
                if not eval_result["overall_passed"]:
                    logging.warning(
                        f"⚠️ Faithfulness check FAILED for question: {question[:50]}...\n"
                        f"   DeepEval score: {eval_result['deepeval_faithfulness']['score']:.2f}\n"
                        f"   Missing values: {eval_result['value_verification']['missing']}"
                    )
                else:
                    logging.info(f"✅ Faithfulness check PASSED (score: {eval_result['deepeval_faithfulness']['score']:.2f})")

            return result
        

    
    @traceable(run_type="llm", name="Web Search")
    @observe(as_type="generation")
    async def _web_search(self, messages):
        """
        Async web search
    
        """
        async with self.semaphore:
            resp = await self.openai.responses.create(
                model='gpt-5',
                input=messages,
                tools=[{"type": "web_search"}],
                tool_choice="auto",
                # max_output_tokens=self.max_output_tokens,
                reasoning={"effort": self.reasoning_effort},
                text={"verbosity": self.verbosity},
            )

            # ===================== MONITORING BLOCK
            usage = resp.usage
            # langfuse.update_current_trace(
            #     usage={
            #         "input": usage.prompt_tokens,
            #         "output": usage.completion_tokens,
            #         "total": usage.total_tokens
            #     },
            #     model=AOAI_DEPLOYMENT # Ensure this matches the Model Settings name
            # )
            run_tree = run_helpers.get_current_run_tree()
            if run_tree:
                run_tree.add_metadata({
                    "token_usage": {
                        "prompt_tokens": usage.input_tokens,
                        "completion_tokens": usage.output_tokens,
                        "total_tokens": usage.total_tokens
                    }
                })
            # ===================== MONITORING BLOCK
            
            
            return resp.output_text
    
    @traceable(run_type="llm", name="Synthesize Section")
    @observe(as_type="generation", name="Synthesize Section")
    async def _answer(self, question, ctx_text, k = 5, temperature = 0.2, calculations = None, enhanced=False):

        async with self.semaphore:
            if calculations is None:
                system_msg = (
                    "You are a document synthesis assistant. Your task is to create structured output based ONLY on the provided context snippets.\n\n"
                    "CRITICAL INSTRUCTIONS:\n"
                    "- You must IMMEDIATELY generate the requested output without asking for clarification or confirmation\n"
                    "- Use ONLY the information from the numbered context snippets provided\n"
                    "- When you use a fact from the context, preserve any existing citations like [#1], [#2], [#5, p.41]\n"
                    "- If a specific value is not found in the context, use 'n.a.'\n"
                    "- Follow the formatting instructions in the user message exactly\n"
                    "- If formatting requests a Sources section, include it at the end\n"
                    "- Do NOT ask questions, do NOT request confirmation - simply execute the task\n\n"
                    f"Additional guidelines:\n{self.profile_prompt}"
                )
            else:
                system_msg = (
                    "You are a document synthesis assistant. Your task is to create structured output based ONLY on the provided context snippets.\n\n"
                    "CRITICAL INSTRUCTIONS:\n"
                    "- You must IMMEDIATELY generate the requested output without asking for clarification or confirmation\n"
                    "- Use ONLY the information from the numbered context snippets provided\n"
                    "- When you use a fact from the context, preserve any existing citations like [#1], [#2], [#5, p.41]\n"
                    "- If a specific value is not found in the context, use 'n.a.'\n"
                    "- Follow the formatting instructions in the user message exactly\n"
                    "- If formatting requests a Sources section, include it at the end\n"
                    "- Do NOT ask questions, do NOT request confirmation - simply execute the task\n\n"
                    f"Additional guidelines:\n{self.profile_prompt}"
                    f"\n ======= CALCULATIONS INSTRUCTIONS =======\n {calculations}"
                )
            # Use XML-style tags for better structure (Google AI best practice)
            user_msg = f"""<task>
                {question}
                </task>

                <context_snippets>
                {ctx_text}
                </context_snippets>

                IMPORTANT: Execute the task using ONLY the data in <context_snippets>. Generate the output immediately without asking for clarification.
            """

            client = self.openai
            messages = [
                {"role":"system","content":system_msg},
                {"role":"user","content":user_msg},
            ]

            if enhanced:
                resp = await client.chat.completions.create(
                    model=AOAI_DEPLOYMENT,
                    messages=messages,
                    reasoning_effort="high",
                    max_completion_tokens=26000,
                )
            else:
                resp = await client.chat.completions.create(
                    model=AOAI_DEPLOYMENT,
                    messages=messages,
                    # temperature=temperature
                )
            
            # ===================== MONITORING BLOCK
            usage = resp.usage
            # langfuse.update_current_trace(
            #     usage={
            #         "input": usage.prompt_tokens,
            #         "output": usage.completion_tokens,
            #         "total": usage.total_tokens
            #     },
            #     model=AOAI_DEPLOYMENT # Ensure this matches the Model Settings name
            # )
            run_tree = run_helpers.get_current_run_tree()
            if run_tree:
                run_tree.add_metadata({
                    "token_usage": {
                        "prompt_tokens": usage.prompt_tokens,
                        "completion_tokens": usage.completion_tokens,
                        "total_tokens": usage.total_tokens
                    }
                })
            # ===================== MONITORING BLOCK

            answer = resp.choices[0].message.content
            cited = self._extract_cited_idxs(answer)

            result = {
                "answer": answer,
                "citations":cited,
            }

            # ======================== VALUATION BLOCK
            if self.enable_faithfulness_eval:
                # ctx_text could be a string or list - normalize it
                source_contexts = [ctx_text] if isinstance(ctx_text, str) else ctx_text
                
                eval_result = await self.synthesis_evaluator.evaluate_synthesis(
                    question=question,
                    synthesized_answer=answer,
                    source_contexts=source_contexts,
                    expected_citations=cited  # Citations found in answer
                )
                result["faithfulness_eval"] = eval_result
                self.evaluation_results.append({
                    "type": "synthesis",
                    "question": question[:100],
                    "eval": eval_result
                })
                
                if not eval_result["overall_passed"]:
                    logging.warning(
                        f"⚠️ Synthesis faithfulness FAILED\n"
                        f"   DeepEval score: {eval_result['deepeval_faithfulness']['score']:.2f}"
                    )
                else:
                    logging.info(f"✅ Synthesis faithfulness PASSED")
            # =================================================================

            return result

    @traceable(run_type="llm", name="Synthesize Section Enhanced")
    @observe(as_type="generation", name="Synthesize Section Enhanced")
    async def _answer_enhanced(self, question, ctx_text, k = 5, temperature = 0.2, calculations = None, reasoning_effort = "high", verbosity = "medium"):
        """
        Enhanced synthesis function using Responses API with reasoning capabilities.
        Optimized for complex financial calculations and multi-step reasoning.

        Args:
            question: The task/question to answer
            ctx_text: Context snippets to use
            k: Number of results (unused, kept for signature compatibility)
            temperature: Temperature setting (may be ignored by Responses API)
            calculations: Optional calculation instructions
            reasoning_effort: "low", "medium", or "high" - controls reasoning depth
            verbosity: "low", "medium", or "high" - controls reasoning visibility in logs

        Returns:
            dict with 'answer' and 'citations' keys
        """

        async with self.semaphore:
            if calculations is None:
                system_msg = (
                    "You are a document synthesis assistant. Your task is to create structured output based ONLY on the provided context snippets.\n\n"
                    "CRITICAL INSTRUCTIONS:\n"
                    "- You must IMMEDIATELY generate the requested output without asking for clarification or confirmation\n"
                    "- Use ONLY the information from the numbered context snippets provided\n"
                    "- When you use a fact from the context, preserve any existing citations like [#1], [#2], [#5, p.41]\n"
                    "- If a specific value is not found in the context, use 'n.a.'\n"
                    "- Follow the formatting instructions in the user message exactly\n"
                    "- If formatting requests a Sources section, include it at the end\n"
                    "- Do NOT ask questions, do NOT request confirmation - simply execute the task\n\n"
                    f"Additional guidelines:\n{self.profile_prompt}"
                )
            else:
                system_msg = (
                    "You are a document synthesis assistant. Your task is to create structured output based ONLY on the provided context snippets.\n\n"
                    "CRITICAL INSTRUCTIONS:\n"
                    "- You must IMMEDIATELY generate the requested output without asking for clarification or confirmation\n"
                    "- Use ONLY the information from the numbered context snippets provided\n"
                    "- When you use a fact from the context, preserve any existing citations like [#1], [#2], [#5, p.41]\n"
                    "- If a specific value is not found in the context, use 'n.a.'\n"
                    "- Follow the formatting instructions in the user message exactly\n"
                    "- If formatting requests a Sources section, include it at the end\n"
                    "- Do NOT ask questions, do NOT request confirmation - simply execute the task\n\n"
                    f"Additional guidelines:\n{self.profile_prompt}"
                    f"\n ======= CALCULATIONS INSTRUCTIONS =======\n {calculations}"
                )
            # Use XML-style tags for better structure (Google AI best practice)
            user_msg = f"""<task>
                {question}
                </task>

                <context_snippets>
                {ctx_text}
                </context_snippets>

                IMPORTANT: Execute the task using ONLY the data in <context_snippets>. Generate the output immediately without asking for clarification.
            """

            client = self.openai

            # Responses API uses 'input' instead of 'messages'
            input_messages = [
                {"role":"system","content":system_msg},
                {"role":"user","content":user_msg},
            ]

            # Use Responses API with reasoning
            resp = await client.responses.create(
                model=OPENAI_REASONING_MODEL,  # gpt-5-2 or from env var
                input=input_messages,  # 'input' not 'messages'
                reasoning={"effort": reasoning_effort},  # "high" for maximum reasoning
                text={"verbosity": verbosity},  # Control reasoning visibility in logs
                max_output_tokens=35000,  # Total output token limit
            )

            # ===================== MONITORING BLOCK
            usage = resp.usage
            output_details = getattr(usage, 'output_tokens_details', None)
            reasoning_tokens = None
            text_tokens = None

            if output_details:
                reasoning_tokens = getattr(output_details, 'reasoning_tokens', None)
                text_tokens = getattr(output_details, 'text_tokens', None)
            

            # Responses API has different field names
            run_tree = run_helpers.get_current_run_tree()
            if run_tree:
                run_tree.add_metadata({
                    "model": OPENAI_REASONING_MODEL,
                    "api_type": "responses",
                    "reasoning_effort": reasoning_effort,
                    "verbosity": verbosity,
                    "token_usage": {
                        "input_tokens": usage.input_tokens,  # Not 'prompt_tokens'
                        "output_tokens": usage.output_tokens,  # Not 'completion_tokens'
                        "total_tokens": usage.total_tokens,
                        "reasoning_tokens": reasoning_tokens,
                        "text_tokens": text_tokens
                    }
                })
            # ===================== MONITORING BLOCK

            # Responses API returns output_text directly
            answer = resp.output_text
            cited = self._extract_cited_idxs(answer)

            result = {
                "answer": answer,
                "citations":cited,
            }

            # ======================== EVALUATION BLOCK
            if self.enable_faithfulness_eval:
                # ctx_text could be a string or list - normalize it
                source_contexts = [ctx_text] if isinstance(ctx_text, str) else ctx_text

                eval_result = await self.synthesis_evaluator.evaluate_synthesis(
                    question=question,
                    synthesized_answer=answer,
                    source_contexts=source_contexts,
                    expected_citations=cited  # Citations found in answer
                )
                result["faithfulness_eval"] = eval_result
                self.evaluation_results.append({
                    "type": "synthesis_enhanced",
                    "question": question[:100],
                    "eval": eval_result
                })

                if not eval_result["overall_passed"]:
                    logging.warning(
                        f"⚠️ Enhanced synthesis faithfulness FAILED\n"
                        f"   DeepEval score: {eval_result['deepeval_faithfulness']['score']:.2f}"
                    )
                else:
                    logging.info(f"✅ Enhanced synthesis faithfulness PASSED")
            # =================================================================

            return result

    @traceable(run_type="chain", name="Parallel RAG Loop")
    @observe(as_type="span", name="Parallel RAG Loop")
    async def _sections(self, pairs, calculations = None):

        """
        Calls in parallel multiple sections
        """

        max_entra_na_retries = 1
        base_delay_seconds = 3.0

        batch_size = 5  # Process 2 at a time
        all_answers = []

        async def process_single_pair(q,r):
            """
            Helper function to process one pair with retries

            """

            tries = 0  # ← Fixed: Start at 0 so first attempt has no delay
            while True:
                if tries > 0:
                    # asyncio.sleep allows other functions to work
                    await asyncio.sleep(base_delay_seconds + 0.5 * tries)

                resp = await self._rag_answer(rag_nl=r[0], question=q[0])
                answer_text = resp["answer"]

                # check if there is need for retry
                if not self.has_na(answer_text) or tries >= max_entra_na_retries:
                    return answer_text
                
                tries += 1

        # The loop -> for q, r in pairs: answer = await process_single_pair(q,r) makes us wait for each pair throughout the loop
        # The async.gather triggers all pairs together

        for i in range(0, len(pairs), batch_size):
            batch = pairs[i:i + batch_size]
            logging.info(f"Processing batch {i//batch_size + 1}/{(len(pairs) + batch_size - 1)//batch_size}")

            tasks = [process_single_pair(q,r) for q,r in batch]
            batch_answers = await asyncio.gather(*tasks)
            all_answers.extend(batch_answers)

            if i + batch_size < len(pairs):
                await asyncio.sleep(20.0)
        
        return all_answers
    
    @traceable(run_type="chain", name="Generate Section")
    @observe(as_type="span")
    async def _generate_section(self, section):
        """
        Orchestrate all sections operations
        """

        if section == 'GENERATE BUSINESS OVERVIEW':
            logging.info(f'Started running {section}')

            biz_overview_pairs_flat = list(zip(biz_overview_pairs[1], biz_overview_pairs[0]))
            section_built = await self._sections(pairs=biz_overview_pairs_flat)

            # web search section
            new_section = f'All instructions applies to the company:  {self.company_name}\n\n{biz_overview_web}\n\n Mention in the Beggining of the answer that this is WEBSEARCH SOURCE'
            messages = [
                {"role":"system", "content": default_gpt_prompt},
                {"role":"user", "content": new_section}
            ]

            resp_web = await self._web_search(messages)
            section_built.append(resp_web)

            ctx_text_formatted = "\n\n".join(section_built)

            resp = await self._answer(
                question=biz_overview_mix_formatting,
                ctx_text=ctx_text_formatted,
                temperature=0.4
            )

            logging.info(f'Finished running {section}')
            return resp['answer']
        elif section == 'GENERATE KEY STAKEHOLDERS':
            logging.info(f'Started running {section}')
            stakeholders_pairs_flat = list(zip(stakeholders_pairs[1], stakeholders_pairs[0]))  # [(r, q), (r, q), ...]
            section_built = await self._sections(pairs= stakeholders_pairs_flat)

            #getting web search sections
            new_section = f'All instructions applies to the company: {self.company_name}\n\n{stakeholders_web} \n\n Mention in the Beggining of the answer that this is WEBSEARCH SOURCE'
            messages = [
                {"role": "system", "content": default_gpt_prompt},
                {"role": "user",   "content": new_section},
            ]
            resp_web = await self._web_search(messages)

            section_built.append(resp_web)

            # Join all context sections - they already contain their own citations
            # Just concatenate them so the model can synthesize
            ctx_text_formatted = "\n\n".join(section_built)

            resp = await self._answer(question=stakeholders_web_mix, ctx_text=section_built, temperature=0.4)
            logging.info(f'Finished running {section}')
            return resp['answer']
        elif section == 'GENERATE FINANCIAL HIGHLIGHTS':
            logging.info(f'Started running {section}')
            finance_pairs_flat = list(zip(finance_pairs[1], finance_pairs[0]))  # [(r, q), (r, q), ...]
            section_built = await self._sections(pairs=finance_pairs_flat)
            ctx_text_formatted = "\n\n".join(section_built)

            # Building table with enhanced calculations
            resp = await self._answer_enhanced(
                question=finance_table,
                ctx_text=ctx_text_formatted,
                temperature=0.4,
                calculations=finance_calculations,
                reasoning_effort="medium",  # Maximum reasoning for calculations
                verbosity="medium"  # Show reasoning steps in logs
            )

            # Fetch narrative context for commentary (WHY the numbers changed)
            logging.info(f'Fetching narrative context for commentary')
            commentary_pairs_flat = list(zip(finance_commentary_pairs[1], finance_commentary_pairs[0]))
            commentary_context_built = await self._sections(pairs=commentary_pairs_flat)
            commentary_narrative_ctx = "\n\n".join(commentary_context_built)

            finance_commentary_ctx = f"""
                <Financial Highlights Table>
                {resp['answer']}
                </Financial Highlights Table>

                <Financial Highlights Numerical Context>
                {ctx_text_formatted}
                </Financial Highlights Numerical Context>

                <Narrative Context - Business Reviews and Management Commentary>
                {commentary_narrative_ctx}
                </Narrative Context - Business Reviews and Management Commentary>
            """

            # Building commentary
            resp2 = await self._answer_enhanced(
                question=finance_commentary,
                ctx_text=finance_commentary_ctx,
                temperature=0.4,
                calculations=finance_calculations,
                reasoning_effort="medium",  # Maximum reasoning for calculations
                verbosity="medium"  # Show reasoning steps in logs
            )

            final_resp = "\n\n".join([resp["answer"], resp2["answer"]])

            logging.info(f'Finished running {section}')
            return final_resp
        elif section == 'GENERATE CAPITAL STRUCTURE':
            logging.info(f'Started running {section}')
            capital_pairs_flat = list(zip(capital_pairs[1], capital_pairs[0]))  # [(r, q), (r, q), ...]
            section_built = await self._sections(pairs=capital_pairs_flat)
            ctx_text_formatted = "\n\n".join(section_built)

            # Use enhanced Responses API for complex capital structure analysis
            resp = await self._answer_enhanced(
                question=capital_structure_table,
                ctx_text=ctx_text_formatted,
                temperature=0.4,
                reasoning_effort="medium",  # Maximum reasoning for calculations
                verbosity="medium"  # Show reasoning steps in logs
            )

            # Fetch narrative context for commentary (WHY debt/capital changed)
            logging.info(f'Fetching narrative context for capital structure commentary')
            capital_commentary_pairs_flat = list(zip(capital_commentary_pairs[1], capital_commentary_pairs[0]))
            capital_narrative_built = await self._sections(pairs=capital_commentary_pairs_flat)
            capital_narrative_ctx = "\n\n".join(capital_narrative_built)

            cap_commentary_ctx = f"""
                <Capital Structure Table>
                {resp['answer']}
                </Capital Structure Table>

                <Capital Structure Numerical Context>
                {ctx_text_formatted}
                </Capital Structure Numerical Context>

                <Narrative Context - Debt and Financing Commentary>
                {capital_narrative_ctx}
                </Narrative Context - Debt and Financing Commentary>
            """

            resp2 = await self._answer_enhanced(
                question=capital_structure_commentary,
                ctx_text=cap_commentary_ctx,
                temperature=0.4,
                reasoning_effort="medium",  # Maximum reasoning for calculations
                verbosity="medium"  # Show reasoning steps in logs
            )

            final_resp = "\n\n".join([resp["answer"], resp2["answer"]])

            logging.info(f'Finished running {section}')
            return final_resp
        elif section == 'GENERATE REVENUE SPLIT':
            logging.info(f'Started running {section}')
            revenue_pairs_flat = list(zip(revenue_pairs[1], revenue_pairs[0]))  # [(r, q), (r, q), ...]
            section_built = await self._sections(pairs= revenue_pairs_flat)
            ctx_text_formatted = "\n\n".join(section_built)
            resp = await self._answer(question=section3, ctx_text=ctx_text_formatted, temperature=0.4)
            logging.info(f'Finished running {section}')
            return resp['answer']
        elif section == 'GENERATE PRODUCTS SERVICES OVERVIEW':
            logging.info(f'Started running {section}')
            new_section = f'All instructions applies to the company: {self.company_name}\n\n{section4a}'
            messages = [
                {"role": "system", "content": default_gpt_prompt},
                {"role": "user",   "content": new_section},
            ]
            resp = await self._web_search(messages)
            logging.info(f'Finished running {section}')
            return resp 
        elif section == 'GENERATE GEO FOOTPRINT':
            logging.info(f'Started running {section}')
            new_section = f'All instructions applies to the company: {self.company_name}\n\n{section4b}'
            messages = [
                {"role": "system", "content": default_gpt_prompt},
                {"role": "user",   "content": new_section},
            ]
            resp = await self._web_search(messages)
            logging.info(f'Finished running {section}')
            return resp
        elif section == 'GENERATE DEVELOPMENTS HIGHLIGHTS':
            logging.info(f'Started running {section}')
            new_section = f'All instructions applies to the company: {self.company_name}\n\n{section5}'
            messages = [
                {"role": "system", "content": default_gpt_prompt},
                {"role": "user",   "content": new_section},
            ]
            resp = await self._web_search(messages)
            logging.info(f'Finished running {section}')
            return resp
        
    @traceable(run_type="chain", name="Generate Full Report")
    @observe(name="Generate Full Report")
    async def generate_company_profile(self, bot = False):

        # self.company_name = company_name

        sections = [
            'GENERATE BUSINESS OVERVIEW',
            'GENERATE KEY STAKEHOLDERS',
            'GENERATE FINANCIAL HIGHLIGHTS',
            'GENERATE CAPITAL STRUCTURE',
            'GENERATE REVENUE SPLIT',
            'GENERATE PRODUCTS SERVICES OVERVIEW',
            'GENERATE GEO FOOTPRINT',
            'GENERATE DEVELOPMENTS HIGHLIGHTS',
        ]

        print(f"📋 Total sections to process: {len(sections)}")

        # Create all tasks
        tasks = [self._generate_section(section) for section in sections]
        print(f"✅ Created {len(tasks)} tasks")

        # Run them all in parallel with exception tracking
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Check for exceptions
        for i, (section, result) in enumerate(zip(sections, results)):
            if isinstance(result, Exception):
                print(f"❌ Section '{section}' failed with error: {type(result).__name__}: {result}")
            elif result is None:
                print(f"⚠️ Section '{section}' returned None (no matching condition in _generate_section)")
            else:
                print(f"✅ Section '{section}' completed successfully ({len(result)} chars)")

        print(f"\n✅ Completed {len(results)} sections total")

        self.final_text = "\n\n".join(r for r in results if r)

        if bot:
            return self.final_text

    @traceable(run_type="chain", name="Generate Full Report (Streaming)")
    @observe(name="Generate Full Report (Streaming)")
    async def generate_company_profile_streaming(self):
        """
        Streaming version that yields progress updates as sections complete
        """

        sections = [
            'GENERATE BUSINESS OVERVIEW',
            'GENERATE KEY STAKEHOLDERS',
            'GENERATE FINANCIAL HIGHLIGHTS',
            'GENERATE CAPITAL STRUCTURE',
            'GENERATE REVENUE SPLIT',
            'GENERATE PRODUCTS SERVICES OVERVIEW',
            'GENERATE GEO FOOTPRINT',
            'GENERATE DEVELOPMENTS HIGHLIGHTS',
        ]

        # Human-readable section names
        section_names = {
            'GENERATE BUSINESS OVERVIEW': 'Business Overview',
            'GENERATE KEY STAKEHOLDERS': 'Key Stakeholders',
            'GENERATE FINANCIAL HIGHLIGHTS': 'Financial Highlights',
            'GENERATE CAPITAL STRUCTURE': 'Capital Structure',
            'GENERATE REVENUE SPLIT': 'Revenue Split',
            'GENERATE PRODUCTS SERVICES OVERVIEW': 'Products/Services Overview',
            'GENERATE GEO FOOTPRINT': 'Geographical Footprint',
            'GENERATE DEVELOPMENTS HIGHLIGHTS': 'Key Recent Developments',
        }

        yield f"📋 Starting profile generation for **{self.company_name}**"
        yield f"📊 Total sections: {len(sections)}"

        # Track completed sections
        completed_results = {}
        completed_count = 0
        start_time = time.time()

        # Create tasks with monitoring
        async def process_section_with_updates(section):
            section_start = time.time()
            try:
                result = await self._generate_section(section)
                elapsed = time.time() - section_start
                return section, result, elapsed, None
            except Exception as e:
                elapsed = time.time() - section_start
                return section, None, elapsed, e

        # Split sections into 3 phases to avoid rate limits:
        # Phase 1: All lightweight sections in parallel
        # Phase 2: Capital Structure alone
        # Phase 3: Financial Highlights alone
        heavy_sections = {'GENERATE CAPITAL STRUCTURE', 'GENERATE FINANCIAL HIGHLIGHTS'}
        light_sections = [s for s in sections if s not in heavy_sections]

        phases = [
            ("Phase 1 — General sections", light_sections),
            ("Phase 2 — Capital Structure", ['GENERATE CAPITAL STRUCTURE']),
            ("Phase 3 — Financial Highlights", ['GENERATE FINANCIAL HIGHLIGHTS']),
        ]

        for phase_label, phase_sections in phases:
            yield f"🔄 **{phase_label}** ({', '.join(section_names[s] for s in phase_sections)})"

            tasks = [process_section_with_updates(s) for s in phase_sections]

            for coro in asyncio.as_completed(tasks):
                section, result, elapsed, error = await coro
                completed_count += 1

                if error:
                    yield f"❌ Failed: **{section_names[section]}** - {type(error).__name__}: {str(error)[:100]}"
                    logging.error(f"Section {section} failed: {error}")
                elif result is None:
                    yield f"⚠️ Warning: **{section_names[section]}** returned no content"
                else:
                    completed_results[section] = result
                    mins = int(elapsed // 60)
                    secs = int(elapsed % 60)
                    yield f"✅ Completed ({completed_count}/{len(sections)}): **{section_names[section]}** - {len(result):,} chars in {mins}m {secs}s"

        # Build final text in correct order
        self.final_text = "\n\n".join(
            completed_results[s] for s in sections if s in completed_results
        )

        total_elapsed = time.time() - start_time
        total_mins = int(total_elapsed // 60)
        total_secs = int(total_elapsed % 60)

        yield f"🎉 **Profile generation complete!** ({completed_count}/{len(sections)} sections, {total_mins}m {total_secs}s total)"
        yield f"📄 Total content: {len(self.final_text):,} characters"
        
    def export_evaluation_report(self, output_path: str = None) -> Dict:
        """
        Export all faithfulness evaluation results
        
        Args:
            output_path: Optional JSON file path to save report
        
        Returns:
            Dictionary with evaluation summary
        """
        if not self.enable_faithfulness_eval:
            return {"error": "Faithfulness evaluation not enabled"}
        
        # Calculate summary statistics
        total_tests = len(self.evaluation_results)
        passed = sum(1 for r in self.evaluation_results if r["eval"]["overall_passed"])
        failed = total_tests - passed
        
        rag_tests = [r for r in self.evaluation_results if r["type"] == "rag_answer"]
        synthesis_tests = [r for r in self.evaluation_results if r["type"] == "synthesis"]
        
        avg_faithfulness = sum(
            r["eval"]["deepeval_faithfulness"]["score"]
            for r in self.evaluation_results
        ) / total_tests if total_tests > 0 else 0
    
        report = {
            "company_name": self.company_name,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "summary": {
                "total_tests": total_tests,
                "passed": passed,
                "failed": failed,
                "pass_rate": passed / total_tests if total_tests > 0 else 0,
                "average_faithfulness_score": avg_faithfulness
            },
            "test_breakdown": {
                "rag_answer_tests": len(rag_tests),
                "synthesis_tests": len(synthesis_tests)
            },
            "detailed_results": self.evaluation_results
        }
        
        if output_path:
            import json
            from pathlib import Path

            # Create directory if it doesn't exist
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)

            with open(output_path, 'w') as f:
                json.dump(report, f, indent=2)
            logging.info(f"📊 Evaluation report saved to {output_path}")
        
        return report