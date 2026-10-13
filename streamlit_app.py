"""NOCTURNE — scientific article summarization workspace."""

import json
import os
import re
import sys
import tempfile
from pathlib import Path
from xml.etree import ElementTree as ET

import requests
import streamlit as st

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# Keep local inference independent of optional Langfuse credentials.
os.environ["LANGFUSE_ENABLED"] = "false"

from app.fulltext import fetch_pmc_xml, find_pmc_ids
from app.parser import parse_articles
from app.pdf_ingestion import extract_pdf_article
from app.preprocessing import load_article
from app.pubmed import PubMedClient
from app.summarizer import summarize_article_data

MANIFEST = ROOT / "data" / "selected_articles.json"
OUTPUT_DIR = ROOT / "outputs" / "ui"
OLLAMA_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434").rstrip("/")
MODELS = ["phi4-mini:latest", "qwen2.5:3b"]
SOURCE_MODES = ["Research library", "PubMed search", "Upload PDF"]

st.set_page_config(
    page_title="NOCTURNE | Scientific Intelligence",
    page_icon="◈",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    r"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=Space+Grotesk:wght@400;500;600;700&display=swap');
    :root {
        --bg: #08070c; --panel: #100e17; --panel-raised: #15121d;
        --line: #30283d; --line-soft: #211c2b; --accent: #b7a4d9;
        --accent-bright: #d5c5f2; --muted: #92899f; --text: #f4effb;
    }
    html, body, [class*="css"] { font-family: 'Space Grotesk', sans-serif; }
    .stApp {
        background-color: var(--bg); color: var(--text);
        background-image:
            linear-gradient(rgba(183,164,217,.045) 1px, transparent 1px),
            linear-gradient(90deg, rgba(183,164,217,.045) 1px, transparent 1px),
            radial-gradient(ellipse at 50% 0%, rgba(91,65,125,.19), transparent 58%);
        background-size: 32px 32px, 32px 32px, 100% 650px;
        background-attachment: fixed;
    }
    [data-testid="stHeader"] { background: rgba(8,7,12,.88); }
    [data-testid="stSidebar"] { background: #0a0910; border-right: 1px solid var(--line-soft); }
    [data-testid="stSidebar"] > div:first-child { padding-top: 1.5rem; }
    .block-container { max-width: 1450px; padding-top: 2rem; padding-bottom: 4rem; }
    h1, h2, h3 { color: var(--text) !important; letter-spacing: -.045em !important; }
    p, label, [data-testid="stMarkdownContainer"] { color: #d7d1e1; }
    .mono { font-family: 'DM Mono', monospace; letter-spacing: .09em; text-transform: uppercase; font-size: .69rem; color: var(--muted); }
    .brand { font-size: 1.12rem; font-weight: 700; letter-spacing: .06em; color: #fff; }
    .brand-mark { color: var(--accent); margin-right: .5rem; font-size: 1.25rem; }
    .hero {
        position: relative; overflow: hidden; padding: 2.2rem 2rem;
        border: 1px solid #393047; border-radius: 8px;
        background: linear-gradient(115deg, rgba(49,36,68,.50), rgba(12,10,17,.96) 66%), #100e17;
        margin-bottom: 1.5rem; box-shadow: inset 0 1px 0 rgba(255,255,255,.025), 0 18px 60px rgba(0,0,0,.15);
    }
    .hero:after {
        content: ""; position: absolute; width: 270px; height: 270px; right: -70px; top: -140px;
        border: 1px solid rgba(183,164,217,.23); border-radius: 50%;
        box-shadow: 0 0 0 28px rgba(183,164,217,.025), 0 0 0 58px rgba(183,164,217,.018);
        pointer-events: none;
    }
    .hero-kicker { font-family: 'DM Mono', monospace; font-size: .7rem; color: var(--accent); letter-spacing: .13em; text-transform: uppercase; }
    .hero-title { font-size: clamp(2.2rem, 4vw, 3.8rem); line-height: 1.02; letter-spacing: -.065em; font-weight: 700; margin: 1rem 0 .8rem; max-width: 760px; color: #fff; }
    .hero-title span { color: var(--accent); }
    .hero-copy { color: #aaa2b9; max-width: 620px; line-height: 1.7; font-size: .96rem; }
    .panel { border: 1px solid var(--line-soft); border-radius: 6px; background: rgba(16,14,23,.94); padding: 1.15rem; margin-bottom: 1rem; }
    .section-label { color: var(--accent); font-family: 'DM Mono', monospace; font-size: .68rem; letter-spacing: .12em; text-transform: uppercase; }
    .metric { background: rgba(16,14,23,.94); border: 1px solid var(--line-soft); padding: 1rem; min-height: 92px; border-radius: 6px; }
    .metric-value { font-size: 1.55rem; font-weight: 700; color: var(--text); margin-top: .4rem; }
    div[data-testid="stSelectbox"] > div > div, div[data-testid="stTextInput"] input,
    div[data-testid="stFileUploader"] section, div[data-testid="stTextArea"] textarea {
        background: #100e17; border-color: #393047; color: var(--text); border-radius: 6px;
    }
    div[data-testid="stRadio"] label { color: var(--text); }
    div[data-testid="stButton"] button, div[data-testid="stDownloadButton"] button {
        border-radius: 6px; min-height: 44px; font-weight: 600;
        border: 1px solid #776394; background: #57466f; color: #fff; transition: all .16s ease;
    }
    div[data-testid="stButton"] button:hover, div[data-testid="stDownloadButton"] button:hover {
        background: #6b5687; border-color: var(--accent); color: #fff; box-shadow: 0 0 22px rgba(183,164,217,.12);
    }
    div[data-testid="stExpander"] { background: #100e17; border: 1px solid var(--line-soft); border-radius: 6px; }
    [data-testid="stMetric"] { background: rgba(16,14,23,.88); padding: .8rem; border: 1px solid var(--line-soft); border-radius: 6px; }
    hr { border-color: var(--line-soft); }
    .footer { border-top: 1px solid var(--line-soft); margin-top: 3rem; padding-top: 1rem; color: #797185; font-family: 'DM Mono', monospace; font-size: .66rem; letter-spacing: .06em; }
    #MainMenu, footer { visibility: hidden; }
    </style>
    """,
    unsafe_allow_html=True,
)


@st.cache_data
def get_articles():
    with MANIFEST.open("r", encoding="utf-8") as file:
        return json.load(file)


def ollama_status():
    """Return exact Ollama model tags, including version suffixes."""
    try:
        response = requests.get(f"{OLLAMA_URL}/api/tags", timeout=3)
        response.raise_for_status()
        names = {
            item.get("name", "").strip()
            for item in response.json().get("models", [])
            if item.get("name")
        }
        return True, names
    except (requests.RequestException, ValueError):
        return False, set()


def normalize_model_tag(tag):
    tag = (tag or "").strip()
    return tag if ":" in tag else f"{tag}:latest"


def safe_article_path(record):
    path = (ROOT / record["json_path"]).resolve()
    if not path.is_relative_to(ROOT.resolve()):
        raise ValueError("Article path is outside the project directory.")
    if not path.is_file():
        raise FileNotFoundError(f"Article file not found: {path.name}")
    return path


def safe_filename(value):
    value = re.sub(r"[^A-Za-z0-9_-]+", "_", str(value)).strip("_")
    return value[:100] or "scientific-article"


def parse_pmc_fulltext(xml_data: bytes) -> list[dict]:
    """Extract body section text from PMC XML, avoiding nested-section duplication."""
    root = ET.fromstring(xml_data)
    sections = []
    for sec in root.findall(".//body//sec"):
        title_el = sec.find("./title")
        heading = " ".join("".join(title_el.itertext()).split()) if title_el is not None else "Section"
        pieces = []
        for child in list(sec):
            if child.tag.rsplit("}", 1)[-1] in {"title", "sec"}:
                continue
            text = " ".join("".join(child.itertext()).split())
            if text:
                pieces.append(text)
        body_text = "\n\n".join(pieces)
        if body_text:
            sections.append({"heading": heading, "text": body_text})
    return sections


def make_pubmed_client(email: str) -> PubMedClient:
    email = email.strip()
    if not email or "@" not in email:
        raise ValueError("Enter a valid contact email for NCBI before searching PubMed.")
    return PubMedClient(email=email)


def search_pubmed(query: str, email: str, limit: int) -> list[dict]:
    client = make_pubmed_client(email)
    pmids = client.search(query, max_results=limit)
    if not pmids:
        return []
    records = parse_articles(client.fetch_articles(pmids))
    by_id = {str(record.get("pmid")): record for record in records}
    return [by_id[pmid] for pmid in pmids if pmid in by_id]


def fetch_pubmed_article(record: dict, email: str) -> dict:
    """Prefer PMC full text; gracefully fall back to the PubMed abstract."""
    make_pubmed_client(email)  # Set Entrez.email before calling fulltext helpers.
    pmid = str(record.get("pmid") or "")
    article = {
        "pmid": pmid,
        "pmcid": f"PMID-{pmid}",
        "title": record.get("title") or "Untitled PubMed article",
        "abstract": record.get("abstract") or "",
        "journal": record.get("journal") or "Journal unavailable",
        "publication_year": record.get("publication_year") or "Year unavailable",
        "sections": [],
    }
    try:
        pmc_id = find_pmc_ids([pmid]).get(pmid)
        if pmc_id:
            sections = parse_pmc_fulltext(fetch_pmc_xml(pmc_id))
            if sections:
                article["sections"] = sections
                article["pmcid"] = f"PMC{pmc_id}"
                article["full_text_available"] = True
    except Exception as exc:
        article["full_text_note"] = f"PMC full text could not be retrieved: {exc}"
    if not article["sections"] and article["abstract"]:
        article["sections"] = [{"heading": "Abstract", "text": article["abstract"]}]
        article["full_text_available"] = False
    if not article["abstract"] and article["sections"]:
        article["abstract"] = article["sections"][0]["text"][:4000]
    return article


# Sidebar
with st.sidebar:
    st.markdown('<div class="brand"><span class="brand-mark">◈</span>NOCTURNE</div>', unsafe_allow_html=True)
    st.markdown('<div class="mono">SCIENTIFIC INTELLIGENCE</div>', unsafe_allow_html=True)
    st.markdown("---")
    st.markdown("**Research workspace**")
    st.caption("Section-aware scientific article summarization")
    st.markdown("---")
    connected, installed_models = ollama_status()
    if connected:
        st.success("OLLAMA · CONNECTED")
    else:
        st.error("OLLAMA · OFFLINE")
    st.markdown('<div class="mono">LOCAL INFERENCE</div>', unsafe_allow_html=True)
    st.caption("Your selected model runs through the local Ollama service.")
    st.markdown("---")
    st.caption("NLP ASSIGNMENT 02")
    st.caption("Research · Summarization · Evaluation")


st.markdown(
    """<div class="hero">
        <div class="hero-kicker">◈ &nbsp; Research intelligence / 01</div>
        <div class="hero-title">Every paper has a story.<br><span>Find its signal.</span></div>
        <div class="hero-copy">Transform scientific literature into structured, evidence-aware summaries using locally hosted language models.</div>
    </div>""",
    unsafe_allow_html=True,
)

try:
    articles = get_articles()
except Exception as exc:
    st.error(f"Unable to load the article manifest: {exc}")
    st.stop()
if not articles:
    st.warning("No selected articles were found in the dataset.")
    st.stop()

m1, m2, m3 = st.columns(3)
for col, value, label in [
    (m1, len(articles), "LIBRARY ARTICLES"),
    (m2, len(MODELS), "LOCAL MODEL OPTIONS"),
    (m3, "ON-DEVICE", "INFERENCE MODE"),
]:
    with col:
        st.markdown(
            f'<div class="metric"><div class="mono">{label}</div><div class="metric-value">{value}</div></div>',
            unsafe_allow_html=True,
        )

st.write("")
left, right = st.columns([1, 1.12], gap="large")
selected = None
uploaded_file = None
uploaded_title = ""
pubmed_record = None

with left:
    st.markdown('<div class="section-label">01 / Source configuration</div>', unsafe_allow_html=True)
    st.markdown("### Choose your paper")
    input_mode = st.radio(
        "Choose source",
        SOURCE_MODES,
        horizontal=True,
        label_visibility="collapsed",
        key="source_mode",
    )
    source_key = "NO-SOURCE"
    contact_email = os.getenv("NCBI_EMAIL", "")

    if input_mode == "Research library":
        by_label = {f'{item["pmcid"]} — {item["title"]}': item for item in articles}
        selected_label = st.selectbox("Scientific article", list(by_label.keys()), key="library_article")
        selected = by_label[selected_label]
        st.markdown('<div class="panel">', unsafe_allow_html=True)
        st.markdown('<div class="mono">ARTICLE METADATA</div>', unsafe_allow_html=True)
        st.markdown(f'**{selected["title"]}**')
        st.caption(f'{selected["pmcid"]} · PMID {selected.get("pmid", "N/A")}')
        st.caption(f'{selected.get("journal", "Journal unavailable")} · {selected.get("publication_year", "Year unavailable")}')
        st.markdown("</div>", unsafe_allow_html=True)
        source_key = selected["pmcid"]

    elif input_mode == "PubMed search":
        st.markdown('<div class="panel">', unsafe_allow_html=True)
        st.markdown('<div class="mono">SEARCH NCBI PUBMED</div>', unsafe_allow_html=True)
        contact_email = st.text_input(
            "Contact email for NCBI",
            value=contact_email,
            placeholder="you@example.com",
            help="NCBI Entrez uses this to identify requests. A paid API key is not required for this small-volume use.",
            key="ncbi_contact_email",
        )
        with st.form("pubmed_search_form"):
            query = st.text_input(
                "Search query",
                value=st.session_state.get("pubmed_query", "machine learning AND medical diagnosis"),
                placeholder="e.g. lung cancer AND machine learning",
            )
            limit = st.selectbox("Maximum results", [5, 10, 15, 20], index=0)
            search_clicked = st.form_submit_button("Search PubMed", use_container_width=True)
        if search_clicked:
            if not query.strip():
                st.warning("Enter a PubMed search query.")
            else:
                try:
                    with st.spinner("Searching PubMed and retrieving article metadata…"):
                        found = search_pubmed(query.strip(), contact_email, int(limit))
                    st.session_state["pubmed_query"] = query.strip()
                    st.session_state["pubmed_results"] = found
                    st.session_state.pop("pubmed_result_choice", None)
                    if not found:
                        st.info("PubMed returned no articles for this query.")
                except Exception as exc:
                    st.error(f"PubMed search failed: {exc}")
        results = st.session_state.get("pubmed_results", [])
        if results:
            result_labels = {
                f'{item.get("title", "Untitled")} · PMID {item.get("pmid", "N/A")}': item
                for item in results
            }
            current_label = st.selectbox("Search results", list(result_labels.keys()), key="pubmed_result_choice")
            pubmed_record = result_labels[current_label]
            source_key = f'PMID-{pubmed_record.get("pmid", "unknown")}'
            st.markdown(f'**{pubmed_record.get("title", "Untitled")}**')
            st.caption(
                f'PMID {pubmed_record.get("pmid", "N/A")} · '
                f'{pubmed_record.get("journal") or "Journal unavailable"} · '
                f'{pubmed_record.get("publication_year") or "Year unavailable"}'
            )
            st.caption("Full text is used when a PMC version is available; otherwise the PubMed abstract is summarized.")
        else:
            st.caption("Search results appear here. Your curated library remains available in its own source mode.")
        st.markdown("</div>", unsafe_allow_html=True)

    else:
        st.markdown('<div class="panel">', unsafe_allow_html=True)
        st.markdown('<div class="mono">UPLOAD A SCIENTIFIC PAPER</div>', unsafe_allow_html=True)
        uploaded_file = st.file_uploader(
            "Choose a PDF file",
            type=["pdf"],
            accept_multiple_files=False,
            help="Text-based PDFs are supported. Scanned PDFs require OCR, which is not enabled.",
            key="scientific_pdf_upload",
        )
        uploaded_title = st.text_input(
            "Paper title (optional)",
            placeholder="Enter a title or leave blank to detect it",
            key="uploaded_paper_title",
        )
        if uploaded_file is not None:
            st.caption(f"Selected: {uploaded_file.name} · {uploaded_file.size / 1024:.1f} KB")
            source_key = f"UPLOAD-{Path(uploaded_file.name).stem}"
        else:
            st.caption("PDF files with selectable text are supported.")
            source_key = "UPLOAD-NONE"
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown('<div class="section-label">02 / Inference engine</div>', unsafe_allow_html=True)
    st.markdown("### Configure generation")
    model = st.selectbox(
        "Local model",
        MODELS,
        format_func=lambda name: {"phi4-mini:latest": "Phi-4-mini", "qwen2.5:3b": "Qwen 2.5 · 3B"}.get(name, name),
        key="selected_model",
    )
    installed_normalized = {normalize_model_tag(tag) for tag in installed_models}
    model_installed = normalize_model_tag(model) in installed_normalized
    if connected and not model_installed:
        st.warning(f"Selected model `{model}` was not found. Check `docker exec scientific-ollama ollama list`.")

    source_ready = (
        input_mode == "Research library"
        or (input_mode == "Upload PDF" and uploaded_file is not None)
        or (input_mode == "PubMed search" and pubmed_record is not None)
    )
    generate = st.button(
        "✦  GENERATE FINAL SUMMARY",
        type="primary",
        use_container_width=True,
        disabled=(not connected) or (not source_ready),
    )
    st.caption("Long scientific papers may take several minutes to summarize.")

if generate:
    temp_path = None
    try:
        if not model_installed:
            raise RuntimeError(f"Ollama model `{model}` is not installed. Install it or choose an installed model.")
        os.environ["OLLAMA_MODEL"] = model
        with st.spinner(f"Reading the paper and generating its final summary with {model}…"):
            if input_mode == "Research library":
                article_data = load_article(safe_article_path(selected))
            elif input_mode == "Upload PDF":
                if uploaded_file is None:
                    raise ValueError("Please upload a PDF first.")
                with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as temp_file:
                    temp_file.write(uploaded_file.getvalue())
                    temp_path = Path(temp_file.name)
                article_data = extract_pdf_article(temp_path, title=uploaded_title.strip() or None)
                article_data["pmcid"] = source_key
                if not article_data.get("title"):
                    article_data["title"] = Path(uploaded_file.name).stem
            else:
                if pubmed_record is None:
                    raise ValueError("Search PubMed and select a result first.")
                article_data = fetch_pubmed_article(pubmed_record, contact_email)
                source_key = f'PMID-{article_data.get("pmid", "unknown")}'

            result = summarize_article_data(article_data)

        if not result.get("final_summary", "").strip():
            raise ValueError("The model returned an empty final summary.")

        result["model"] = model
        result["source_type"] = {
            "Research library": "library",
            "PubMed search": "pubmed",
            "Upload PDF": "uploaded_pdf",
        }[input_mode]
        result["pmcid"] = article_data.get("pmcid", source_key)
        result["pmid"] = article_data.get("pmid")
        result["title"] = article_data.get("title", "Scientific article")
        result["journal"] = article_data.get("journal")
        result["publication_year"] = article_data.get("publication_year")
        if article_data.get("full_text_note"):
            result["full_text_note"] = article_data["full_text_note"]
        result["full_text_available"] = article_data.get("full_text_available")

        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        output_path = OUTPUT_DIR / f'{safe_filename(result["pmcid"])}_{safe_filename(model)}.json'
        output_path.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
        st.session_state["nocturne_result"] = result
        st.session_state["nocturne_result_key"] = (source_key, model)
        st.session_state["nocturne_result_path"] = str(output_path)
        st.success("Final summary generated and saved.")
    except Exception as exc:
        st.error(f"Summary generation failed: {exc}")
        st.caption("Check the PowerShell logs, PDF text extraction, PubMed connectivity, and Ollama model availability.")
    finally:
        if temp_path is not None:
            temp_path.unlink(missing_ok=True)

# Shared results renderer for every input source.
result = st.session_state.get("nocturne_result")
result_key = st.session_state.get("nocturne_result_key")
current_key = (source_key, model)

if result and result_key == current_key:
    st.markdown("---")
    st.markdown('<div class="section-label">03 / Research output</div>', unsafe_allow_html=True)
    st.markdown("## Summary workspace")
    a, b, c = st.columns(3)
    a.metric("Model", result.get("model", model))
    b.metric("Chunks processed", result.get("chunk_count", "—"))
    source_labels = {"library": "Research library", "pubmed": "PubMed", "uploaded_pdf": "Uploaded PDF"}
    c.metric("Source", source_labels.get(result.get("source_type"), result.get("pmcid", "—")))

    if result.get("source_type") == "pubmed":
        st.caption(
            f'PMID: {result.get("pmid") or "N/A"} · '
            f'{result.get("journal") or "Journal unavailable"} · '
            f'{result.get("publication_year") or "Year unavailable"}'
        )
        if result.get("full_text_available") is False:
            st.info("This paper was summarized from its PubMed abstract because PMC full text was unavailable.")
        if result.get("full_text_note"):
            st.caption(result["full_text_note"])

    st.markdown('<div class="panel">', unsafe_allow_html=True)
    st.markdown('<div class="mono">GENERATED FINAL SUMMARY</div>', unsafe_allow_html=True)
    st.markdown(f'### {result.get("title", "Scientific article summary")}')
    st.markdown(result.get("final_summary", "No summary available."))
    st.markdown("</div>", unsafe_allow_html=True)

    summary_md = (
        f'# {result.get("title", "Scientific Article Summary")}\n\n'
        f'**Source:** {result.get("pmcid", "")}  \n'
        f'**PMID:** {result.get("pmid") or "N/A"}  \n'
        f'**Journal:** {result.get("journal") or "N/A"}  \n'
        f'**Year:** {result.get("publication_year") or "N/A"}  \n'
        f'**Model:** {result.get("model", model)}\n\n'
        f'{result.get("final_summary", "")}\n'
    )
    d1, d2 = st.columns(2)
    with d1:
        st.download_button(
            "↓  DOWNLOAD MARKDOWN",
            data=summary_md,
            file_name=f'{safe_filename(result.get("pmcid", "article"))}_summary.md',
            mime="text/markdown",
            use_container_width=True,
        )
    with d2:
        st.download_button(
            "↓  DOWNLOAD JSON",
            data=json.dumps(result, indent=2, ensure_ascii=False),
            file_name=f'{safe_filename(result.get("pmcid", "article"))}_{safe_filename(model)}.json',
            mime="application/json",
            use_container_width=True,
        )

    with st.expander("Inspect section-level chunk summaries"):
        for index, chunk in enumerate(result.get("chunk_summaries", []), start=1):
            st.markdown(f'**CHUNK {index:02d}**')
            st.write(chunk)
            st.markdown("---")
elif result and result_key != current_key:
    st.info("Your previous result is saved. Generate a summary for the currently selected source and model to display it here.")

st.markdown(
    '<div class="footer">NOCTURNE / SCIENTIFIC ARTICLE SUMMARIZATION · LOCAL INFERENCE · NLP ASSIGNMENT 02</div>',
    unsafe_allow_html=True,
)