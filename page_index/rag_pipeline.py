
import pymupdf4llm
import os
import sys
import json
import asyncio
import argparse
from typing import Optional

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

# Add the pageindex repo to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "pageindex_repo"))
from pageindex import page_index_main, page_index
from pageindex.page_index_md import md_to_tree
from pageindex.utils import (
    get_nodes,
    get_leaf_nodes,
    write_node_id,
    remove_fields,
    add_node_text,
    get_page_tokens,
)

load_dotenv()

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY") or os.getenv("CHATGPT_API_KEY")
MODEL_NAME = os.getenv("OPENAI_MODEL", "gpt-4o-2024-11-20")

if not OPENAI_API_KEY:
    raise EnvironmentError(
        "Set OPENAI_API_KEY or CHATGPT_API_KEY in your .env file."
    )


# ---------------------------------------------------------------------------
# Step 1: OCR  -  PDF -> Markdown
# ---------------------------------------------------------------------------

def _pdf_has_text(pdf_path: str) -> bool:
    """Check if a PDF has an actual text layer (vs scanned images)."""
    import pymupdf
    doc = pymupdf.open(pdf_path)
    # Check first few pages for text
    for i in range(min(3, len(doc))):
        if doc[i].get_text().strip():
            doc.close()
            return True
    doc.close()
    return False


def _ocr_with_vision(pdf_path: str) -> str:
    """OCR a scanned PDF using GPT-4o vision. Returns markdown text."""
    import pymupdf
    import base64
    from openai import OpenAI

    client = OpenAI(api_key=OPENAI_API_KEY)
    doc = pymupdf.open(pdf_path)
    total_pages = len(doc)
    all_markdown = []

    print(f"  [OCR] Using GPT-4o vision for {total_pages} pages ...")

    for page_num in range(total_pages):
        page = doc[page_num]
        # Render page to image at 200 DPI for good quality
        pix = page.get_pixmap(dpi=200)
        img_bytes = pix.tobytes("png")
        b64_image = base64.b64encode(img_bytes).decode("utf-8")

        print(f"  [OCR] Page {page_num + 1}/{total_pages} ...", end="", flush=True)

        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a document OCR system. Convert the page image to "
                        "well-structured markdown. Preserve all text exactly as written. "
                        "Use markdown headings (#, ##, ###) for section titles. "
                        "Use markdown tables for any tables. "
                        "Preserve numbers, dates, and currency values exactly. "
                        "Do NOT add commentary or summaries - just transcribe."
                    ),
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/png;base64,{b64_image}",
                                "detail": "high",
                            },
                        },
                        {
                            "type": "text",
                            "text": "Convert this page to markdown. Preserve all text, tables, and structure exactly.",
                        },
                    ],
                },
            ],
            max_tokens=4096,
            temperature=0,
        )

        page_md = response.choices[0].message.content.strip()
        all_markdown.append(f"<!-- Page {page_num + 1} -->\n\n{page_md}")
        print(" done")

    doc.close()
    return "\n\n---\n\n".join(all_markdown)


def pdf_to_markdown(pdf_path: str, output_dir: str = "./markdown_output") -> str:
    """Convert a PDF to markdown. Uses pymupdf4llm for text PDFs, GPT-4o vision for scans."""
    os.makedirs(output_dir, exist_ok=True)
    pdf_name = os.path.splitext(os.path.basename(pdf_path))[0]
    md_path = os.path.join(output_dir, f"{pdf_name}.md")

    # Skip if already converted AND has content
    if os.path.exists(md_path) and os.path.getsize(md_path) > 100:
        print(f"  [OCR] Markdown already exists, skipping: {md_path}")
        return md_path

    if _pdf_has_text(pdf_path):
        # Standard text extraction
        import pymupdf4llm
        print(f"  [OCR] Text PDF detected, using pymupdf4llm ...")
        md_text = pymupdf4llm.to_markdown(pdf_path)
    else:
        # Scanned PDF - use GPT-4o vision
        print(f"  [OCR] Scanned PDF detected (no text layer)")
        md_text = _ocr_with_vision(pdf_path)

    with open(md_path, "w", encoding="utf-8") as f:
        f.write(md_text)
    print(f"  [OCR] Saved: {md_path} ({len(md_text):,} chars)")
    return md_path


# ---------------------------------------------------------------------------
# Step 2: PDF -> Markdown (OCR) -> PageIndex tree
# ---------------------------------------------------------------------------
from unstructured.partition.pdf import partition_pdf
async def build_tree_from_pdf(pdf_path: str, results_dir: str = "./results") -> dict:
    os.makedirs(results_dir, exist_ok=True)
    pdf_name = os.path.basename(pdf_path)
    cache_path = os.path.join(results_dir, f"{pdf_name}_structure.json")

    if os.path.exists(cache_path): os.remove(cache_path)

    print(f"\n  [OCR] STARTING MANUAL STRUCTURE EXTRACTION: {pdf_name}")
    try:
        elements = partition_pdf(filename=pdf_path, strategy="hi_res", infer_table_structure=True)
        
        nodes = []
        current_node = {"node_id": "root", "title": "Document Start", "text": "", "nodes": []}
        node_counter = 1
        last_page = 1

        for el in elements:
            page = el.metadata.page_number if el.metadata.page_number else last_page
            last_page = page
            content = el.text.strip()
            if not content: continue

            if (content.isupper() and len(content) < 120) or el.category == "Title":
                # Save the previous node before starting a new one
                nodes.append(current_node)
                current_node = {
                    "node_id": f"node_{node_counter}",
                    "title": content,
                    "text": f"Page {page}: ",
                    "nodes": []
                }
                node_counter += 1
            
            # Add text/tables to the active node
            if el.category == "Table":
                current_node["text"] += f"\n{el.metadata.text_as_html}\n"
            else:
                current_node["text"] += f"{content} "

        nodes.append(current_node) # Append the final node

        # Manually assemble the tree to bypass the PageIndex math crash
        tree = {
            "node_id": "root_container",
            "title": pdf_name,
            "text": "Main Document Container",
            "nodes": nodes
        }

        with open(cache_path, "w", encoding="utf-8") as f:
            json.dump(tree, f, indent=2)
        
        print(f"  [SUCCESS] FORCED TREE BUILT: {len(nodes)} sections found.")
        return tree

    except Exception as e:
        print(f"  [ERROR] Manual Extraction Failed: {e}")
        return {"node_id": "root", "title": "Error Fallback", "text": "Empty", "nodes": []}

# ---------------------------------------------------------------------------
# Step 3: Tree-based retrieval using LangChain
# ---------------------------------------------------------------------------

def build_node_map(tree: dict) -> dict:
    """Create a flat mapping of node_id -> node for quick lookups."""
    node_map = {}

    def _walk(node):
        nid = node.get("node_id")
        if nid:
            node_map[nid] = node
        for child in node.get("nodes", []):
            _walk(child)

    if isinstance(tree, list):
        for item in tree:
            _walk(item)
    else:
        _walk(tree)
    return node_map


def get_tree_skeleton(tree: dict) -> dict:
    """Return tree without text fields (for the search prompt)."""
    import copy
    skeleton = copy.deepcopy(tree)
    if isinstance(skeleton, list):
        for item in skeleton:
            _strip_text(item)
    else:
        _strip_text(skeleton)
    return skeleton


def _strip_text(node: dict):
    node.pop("text", None)
    for child in node.get("nodes", []):
        _strip_text(child)


def create_tree_search_chain():
    """LangChain chain that searches a PageIndex tree for relevant nodes."""
    llm = ChatOpenAI(
        model=MODEL_NAME,
        api_key=OPENAI_API_KEY,
        temperature=0,
    )

    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are a document retrieval expert. Given a query and a document tree structure, identify all nodes likely to contain relevant information."),
        ("human", """Find all nodes in this document tree that are relevant to the query.

Query: {query}

Document tree structure:
{tree_skeleton}

Reply ONLY in this JSON format (no markdown fences):
{{
  "thinking": "<your reasoning about which nodes are relevant>",
  "node_list": ["node_id_1", "node_id_2"]
}}"""),
    ])

    chain = prompt | llm | StrOutputParser()
    return chain


def create_answer_chain():
    """LangChain chain that answers a question given retrieved context."""
    llm = ChatOpenAI(
        model=MODEL_NAME,
        api_key=OPENAI_API_KEY,
        temperature=0,
    )

    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are a financial analyst. Answer questions accurately using ONLY the provided context. Always cite sources with page references where available."),
        ("human", """Answer the following question using ONLY the context below.
If the information is not available, say so clearly.

Question: {question}

Context:
{context}

Provide a clear, detailed answer with source citations."""),
    ])

    chain = prompt | llm | StrOutputParser()
    return chain


async def retrieve_from_tree(
    query: str,
    tree: dict,
    node_map: dict,
    search_chain,
) -> tuple[list[str], str]:
    """
    Use the tree-search chain to find relevant nodes from our MANUAL tree.
    """
    skeleton = {
        "nodes": [
            {"node_id": n["node_id"], "title": n["title"]} 
            for n in tree.get("nodes", [])
        ]
    }
    skeleton_json = json.dumps(skeleton, indent=2, ensure_ascii=False)

    result_text = await search_chain.ainvoke({
        "query": query,
        "tree_skeleton": skeleton_json,
    })

    try:
        clean = result_text.strip()
        if clean.startswith("```"):
            clean = clean.split("\n", 1)[1]
        if clean.endswith("```"):
            clean = clean.rsplit("```", 1)[0]
        result_json = json.loads(clean)
    except json.JSONDecodeError:
        # Fallback: if retrieval fails, give the first 5 sections (likely where main data is)
        print(f"  [WARN] Tree search failed to pick nodes, defaulting to first 5.")
        result_json = {"node_list": [n["node_id"] for n in tree.get("nodes", [])[:5]]}

    node_ids = result_json.get("node_list", [])

    # Extract text from the manually created node map
    context_parts = []
    valid_node_ids = []
    for nid in node_ids:
        # Check both string and integer IDs to be safe
        node = node_map.get(nid) or node_map.get(str(nid))
        if node and "text" in node:
            title = node.get("title", "Unknown Section")
            # We skip start/end index because we manually hardcoded the page into the 'text'
            context_parts.append(f"Section: {title}\nContent: {node['text']}")
            valid_node_ids.append(nid)

    context = "\n\n---\n\n".join(context_parts) if context_parts else "No relevant content found."
    return valid_node_ids, context


async def rag_query(
    query: str,
    tree: dict,
    node_map: dict,
    search_chain,
    answer_chain,
    llm_question: Optional[str] = None,
) -> dict:
    """
    Full RAG pipeline: tree search -> context extraction -> LLM answer.

    Args:
        query: The search/retrieval query (used for tree search)
        tree: The PageIndex tree structure
        node_map: Flat node_id -> node mapping
        search_chain: LangChain chain for tree search
        answer_chain: LangChain chain for answer generation
        llm_question: Optional refined question for the LLM (if different from query)

    Returns dict with: query, question, node_ids, context, answer
    """
    question = llm_question or query

    node_ids, context = await retrieve_from_tree(query, tree, node_map, search_chain)

    answer = await answer_chain.ainvoke({
        "question": question,
        "context": context,
    })

    return {
        "query": query,
        "question": question,
        "node_ids": node_ids,
        "context_length": len(context),
        "answer": answer,
    }


# ---------------------------------------------------------------------------
# Step 4: Run RAG on section prompt pairs
# ---------------------------------------------------------------------------

async def run_section_pairs(
    pairs: tuple,
    tree: dict,
    node_map: dict,
    search_chain,
    answer_chain,
    section_name: str = "section",
) -> list[dict]:
    """
    Run RAG for a set of (rag_queries, llm_questions) pairs.
    pairs is a tuple of (rag_queries_list, llm_questions_list).
    """
    rag_queries = pairs[0]
    llm_questions = pairs[1] if len(pairs) > 1 else rag_queries

    results = []
    for i, (rq, lq) in enumerate(zip(rag_queries, llm_questions)):
        rag_q = rq[0] if isinstance(rq, list) else rq
        llm_q = lq[0] if isinstance(lq, list) else lq

        print(f"  [{section_name}] Query {i+1}/{len(rag_queries)}: {rag_q[:80]}...")
        result = await rag_query(rag_q, tree, node_map, search_chain, answer_chain, llm_q)
        result["section"] = section_name
        result["pair_index"] = i
        results.append(result)

    return results


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

async def process_documents(pdf_dir: str, ad_hoc_query: Optional[str] = None):
    """Process all PDFs and run the RAG pipeline."""
    # Find PDFs
    pdf_files = sorted([
        os.path.join(pdf_dir, f)
        for f in os.listdir(pdf_dir)
        if f.lower().endswith(".pdf")
    ])

    if not pdf_files:
        print(f"No PDF files found in {pdf_dir}")
        return

    print(f"Found {len(pdf_files)} PDF(s)\n")

    # Initialize LangChain chains
    search_chain = create_tree_search_chain()
    answer_chain = create_answer_chain()

    all_results = []

    for pdf_path in pdf_files:
        pdf_name = os.path.basename(pdf_path)
        print(f"\n{'='*60}")
        print(f"Processing: {pdf_name}")
        print(f"{'='*60}")

        try:
            tree = await build_tree_from_pdf(pdf_path)
        except Exception as e:
            print(f"  [ERROR] PageIndex failed to process {pdf_name}: {e}")
            print(f"  Skipping this PDF.")
            continue

        # Build node map
        node_map = build_node_map(tree)
        print(f"  Tree has {len(node_map)} nodes")

        if len(node_map) == 0:
            print(f"  [WARN] No nodes found in tree. PDF may be too short or simple.")
            print(f"  Skipping this PDF.")
            continue

        if ad_hoc_query:
            # Single query mode
            result = await rag_query(
                ad_hoc_query, tree, node_map, search_chain, answer_chain
            )
            result["document"] = pdf_name
            all_results.append(result)
            print(f"\n  Answer:\n{result['answer']}")
        else:
            # Run all section pairs from section_prompts
            from section_prompts import (
                finance_pairs,
                capital_pairs,
                stakeholders_pairs,
                biz_overview_pairs,
                revenue_pairs,
                finance_commentary_pairs,
                capital_commentary_pairs,
            )

            section_configs = [
                (finance_pairs, "finance"),
                (capital_pairs, "capital_structure"),
                (stakeholders_pairs, "stakeholders"),
                (biz_overview_pairs, "business_overview"),
                (revenue_pairs, "revenue"),
                (finance_commentary_pairs, "finance_commentary"),
                (capital_commentary_pairs, "capital_commentary"),
            ]

            for pairs, name in section_configs:
                print(f"\n--- Running {name} ---")
                results = await run_section_pairs(
                    pairs, tree, node_map, search_chain, answer_chain, name
                )
                for r in results:
                    r["document"] = pdf_name
                all_results.extend(results)

    # Save all results
    os.makedirs("./results", exist_ok=True)
    output_path = "./results/rag_results.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(all_results, f, indent=2, ensure_ascii=False)
    print(f"\nAll results saved to {output_path}")

    return all_results


def main():
    parser = argparse.ArgumentParser(description="PageIndex + LangChain RAG Pipeline")
    parser.add_argument("--pdf_dir", type=str, default=".", help="Directory with PDF files")
    parser.add_argument("--query", type=str, help="Single ad-hoc query (runs against all PDFs)")
    args = parser.parse_args()

    asyncio.run(process_documents(args.pdf_dir, args.query))


if __name__ == "__main__":
    main()
