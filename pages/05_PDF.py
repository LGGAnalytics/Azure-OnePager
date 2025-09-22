from io import BytesIO
from typing import Tuple
import time
import streamlit as st

from engines.hybrig_eng_enhanced import HybridEngine
# from engines.engine1_enhanced import EngineApprentice

# ---- Cached builders -------------------------------------------------------
@st.cache_resource(show_spinner=False)
def ocr_engine_cached_multi(files_bytes: Tuple[bytes, ...], files_names: Tuple[str, ...]):
    """Multi-file OCR mode via HybridEngine (idempotent + timed)."""
    pdf_streams = tuple((BytesIO(b), n) for b, n in zip(files_bytes, files_names))
    engine = HybridEngine(pdf_streams)
    t0 = time.perf_counter(); engine.main(); build_s = time.perf_counter() - t0
    timings = getattr(engine, "timings", {})
    timings["total_build_s"] = build_s
    return engine.chain, engine.chain_with_sources, timings


# ---- App -------------------------------------------------------------------
def main():
    st.set_page_config(page_title="Oraculum")
    st.title("Oraculum")
    output_placeholder = st.empty()

    st.write(
        "Available engines: \n"
        "1. Text Engine (fast, text-only; multi-PDF) \n"
        "2. OCR Engine (hybrid OCR; multi-PDF)\n"
        "Upload one or more PDFs and select an engine."
    )

    for key in ("ocr_mode", "text_engine", "processed"):
        if key not in st.session_state:
            st.session_state[key] = False

    pdf_files = st.file_uploader("Upload your PDF(s)", type=["pdf"], accept_multiple_files=True)
    col1, col2 = st.columns(2)

    if col1.button("OCR Engine"):
        st.session_state.update({"ocr_mode": True, "text_engine": False, "processed": False})

    # --- OCR Engine (multi-file) -------------------------------------------
    if st.session_state.ocr_mode and pdf_files:
        # IMPORTANT: use getvalue() so cache keys are stable across reruns
        files_bytes: Tuple[bytes, ...] = tuple(f.getvalue() for f in pdf_files)
        files_names: Tuple[str, ...] = tuple(f.name for f in pdf_files)

        if not st.session_state.processed:
            with st.spinner("Building OCR (hybrid) index across all PDFs..."):
                chain, chain_src, timings = ocr_engine_cached_multi(files_bytes, files_names)
                st.session_state.ocr_chain = chain
                st.session_state.ocr_chain_with_sources = chain_src
                st.session_state.ocr_timings = timings
            st.success("OCR index ready.")
            st.session_state.processed = True

        st.subheader("Timings")
        st.json(st.session_state.ocr_timings)

        question = st.text_input("Ask a question about your PDFs:")
        if question:
            res = st.session_state.ocr_chain_with_sources.invoke(question)
            st.write(res["response"])

if __name__ == "__main__":
    main()