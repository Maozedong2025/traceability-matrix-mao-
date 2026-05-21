import re
import streamlit as st
import pandas as pd

from config import APP_TITLE, APP_SUBTITLE, VALIDATION_CATEGORIES
from services.file_utils import save_uploaded_file
from services.text_extractor import extract_full_text, get_content_summary
from services.agent_orchestrator import run_agent_pipeline
from services.item_extractor import extract_items
from services.mapping_engine import generate_traceability_matrix, generate_forward_mapping, generate_downstream_mapping
from services.gap_analyzer import generate_gap_report
from services.export_service import export_excel

st.set_page_config(page_title=APP_TITLE, layout="wide")

st.markdown("""
<style>
.main-title{font-size:34px;font-weight:800;color:#0f172a;margin-bottom:4px}
.sub-title{font-size:16px;color:#475569;margin-bottom:18px}
.compliance-box{background:#fff7ed;border-left:5px solid #f97316;padding:12px 16px;border-radius:8px;color:#7c2d12;font-size:15px}
.section-card{background:white;border:1px solid #e2e8f0;border-radius:16px;padding:18px;margin-top:18px;box-shadow:0 2px 12px rgba(15,23,42,.06)}
div[data-testid="stFileUploader"] section{border:2px dashed #ef4444!important;background:#fff1f2!important;border-radius:14px!important}
div[data-testid="stFileUploader"] button{background-color:#dc2626!important;color:white!important;border-radius:10px!important;border:none!important}
.stButton>button{border-radius:10px;font-weight:700}
button[kind="primary"]{background-color:#2563eb!important;color:white!important}
</style>
""", unsafe_allow_html=True)

for key, default in {
    "documents": [], "agent_state": {}, "items": [], "matrix": [], "forward": [], "downstream": [], "gaps": []
}.items():
    if key not in st.session_state:
        st.session_state[key] = default

st.markdown(f'<div class="main-title">{APP_TITLE}</div>', unsafe_allow_html=True)
st.markdown(f'<div class="sub-title">{APP_SUBTITLE}</div>', unsafe_allow_html=True)
st.markdown('<div class="compliance-box"><b>Compliance note:</b> AI/RAG output is a draft suggestion only. QA/Validation review is required before official industrial or life-science use.</div>', unsafe_allow_html=True)

tabs = st.tabs(["1. Upload & Agent Check","2. Confirm Categories","3. Extracted Items","4. Matrix","5. Forward Mapping","6. Downstream Mapping","7. Gap Report","8. Export","9. Ask Agent"])

with tabs[0]:
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.subheader("1. Upload Documents and Let Agent Check Files")
    st.write("Upload URS, FRS/FS, DS, IQ, OQ, PQ, or SOP documents. Invalid business data files will be rejected.")
    uploaded = st.file_uploader("Upload validation documents", type=["pdf","docx","xlsx","xls","csv","txt"], accept_multiple_files=True)
    if uploaded and st.button("Process documents", type="primary"):
        with st.spinner("processing... Agent is checking files, extracting text, validating documents, and predicting categories"):
            docs = []
            for f in uploaded:
                try:
                    path = save_uploaded_file(f)
                    extracted = extract_full_text(path)
                    docs.append({
                        "file_name": f.name, "file_path": path, "full_text": extracted["full_text"],
                        "chunks": extracted.get("chunks", []), "summary": get_content_summary(extracted["full_text"])
                    })
                except Exception as e:
                    docs.append({"file_name": f.name, "file_path": "", "full_text": "", "chunks": [], "summary": {}, "is_valid": False, "rejection_reason": str(e)})
            state = run_agent_pipeline(docs)
            st.session_state["documents"] = state.get("documents", [])
            st.session_state["agent_state"] = state
            st.session_state["items"] = state.get("items", [])
            st.session_state["matrix"] = state.get("matrix", [])
            st.session_state["forward"] = state.get("forward", [])
            st.session_state["downstream"] = state.get("downstream", [])
            st.session_state["gaps"] = state.get("gaps", [])
        st.success("processing completed. Agent workflow finished.")

    if st.session_state["documents"]:
        st.subheader("Agent Status")
        for msg in st.session_state.get("agent_state", {}).get("messages", []):
            st.info(msg)
        inv, rej = [], []
        for d in st.session_state["documents"]:
            row = {
                "File Name": d.get("file_name"), "Valid": d.get("is_valid"),
                "Predicted Category": d.get("predicted_category"), "Confirmed Category": d.get("confirmed_category"),
                "Words": d.get("summary", {}).get("word_count"),
                "Reason": d.get("classification_reason") or d.get("rejection_reason") or d.get("validation_check",{}).get("reason","")
            }
            (inv if d.get("is_valid") else rej).append(row)
        if inv:
            st.subheader("Valid Document Inventory")
            st.dataframe(pd.DataFrame(inv), use_container_width=True)
        if rej:
            st.error("Invalid document(s) rejected. Only URS, FRS/FS, DS, IQ, OQ, PQ, and SOP documents are accepted.")
            st.dataframe(pd.DataFrame(rej), use_container_width=True)
        with st.expander("Extracted content preview"):
            for d in st.session_state["documents"]:
                st.markdown(f"**{d.get('file_name')}**")
                st.code(d.get("summary", {}).get("preview", "")[:2000])
    st.markdown('</div>', unsafe_allow_html=True)

with tabs[1]:
    st.subheader("2. Confirm or Correct Document Categories")
    docs = st.session_state["documents"]
    if not docs:
        st.warning("Upload and process documents first.")
    else:
        for idx, d in enumerate(docs):
            if not d.get("is_valid"):
                st.warning(f"{d.get('file_name')} was rejected: {d.get('rejection_reason') or d.get('validation_check',{}).get('reason','')}")
                continue
            c1,c2,c3 = st.columns([3,2,3])
            c1.write(f"**{d.get('file_name')}**")
            c2.write(f"Predicted: **{d.get('predicted_category')}**")
            current = d.get("confirmed_category") if d.get("confirmed_category") in VALIDATION_CATEGORIES else d.get("predicted_category")
            d["confirmed_category"] = c3.selectbox("Confirmed category", VALIDATION_CATEGORIES, index=VALIDATION_CATEGORIES.index(current) if current in VALIDATION_CATEGORIES else 0, key=f"cat_{idx}")
        if st.button("Apply category corrections and re-run extraction/mapping", type="primary"):
            with st.spinner("processing... Re-extracting items and regenerating matrix"):
                all_items = []
                for d in docs:
                    if d.get("is_valid"):
                        all_items.extend(extract_items(d.get("full_text",""), d.get("confirmed_category",""), d.get("file_name",""), d.get("chunks", [])))
                matrix = generate_traceability_matrix(all_items)
                st.session_state["items"] = all_items
                st.session_state["matrix"] = matrix
                st.session_state["forward"] = generate_forward_mapping(matrix)
                st.session_state["downstream"] = generate_downstream_mapping(matrix)
                st.session_state["gaps"] = generate_gap_report(docs, matrix, all_items)
            st.success("processing completed. Categories applied and matrix regenerated.")

with tabs[2]:
    st.subheader("3. Extracted Items")
    if st.session_state["items"]:
        st.dataframe(pd.DataFrame(st.session_state["items"]), use_container_width=True)
        st.info("AUTO-generated IDs indicate messy extraction and require human review.")
    else:
        st.warning("No extracted items available.")

with tabs[3]:
    st.subheader("4. Traceability Matrix")
    if st.session_state["matrix"]:
        st.dataframe(pd.DataFrame(st.session_state["matrix"]), use_container_width=True)
    else:
        st.warning("No matrix generated yet.")

with tabs[4]:
    st.subheader("5. Forward Mapping")
    st.write("Direct links from URS to FRS, DS, IQ, OQ, and PQ.")
    if st.session_state["forward"]:
        st.dataframe(pd.DataFrame(st.session_state["forward"]), use_container_width=True)
    else:
        st.warning("No forward mapping available.")

with tabs[5]:
    st.subheader("6. Downstream Mapping")
    st.write("Lifecycle chains like URS → FRS → DS → IQ → OQ → PQ.")
    if st.session_state["downstream"]:
        st.dataframe(pd.DataFrame(st.session_state["downstream"]), use_container_width=True)
    else:
        st.warning("No downstream mapping available.")

with tabs[6]:
    st.subheader("7. Gap Report")
    if st.session_state["gaps"]:
        st.dataframe(pd.DataFrame(st.session_state["gaps"]), use_container_width=True)
    else:
        st.success("No gaps found.")

with tabs[7]:
    st.subheader("8. Export")
    if st.session_state["matrix"]:
        summary = [{
            "Total Valid Documents": len([d for d in st.session_state["documents"] if d.get("is_valid")]),
            "Rejected Documents": len([d for d in st.session_state["documents"] if not d.get("is_valid")]),
            "Total Extracted Items": len(st.session_state["items"]),
            "Total URS Rows": len(st.session_state["matrix"]),
            "Total Gaps": len(st.session_state["gaps"]),
            "Compliance Note": "AI/RAG generated draft only. QA/Validation review required."
        }]
        excel = export_excel(summary, st.session_state["matrix"], st.session_state["forward"], st.session_state["downstream"], st.session_state["gaps"], st.session_state["documents"], st.session_state["items"])
        st.download_button("Download Final Traceability Matrix Excel", data=excel, file_name="traceability_matrix_langgraph_agent.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", type="primary")
    else:
        st.warning("Generate matrix before export.")

with tabs[8]:
    st.subheader("9. Ask Traceability Agent")
    st.write("Ask about a specific ID, mapping, gaps, rejected files, or auto-generated IDs.")
    q = st.text_input("Ask a question", placeholder="Example: what is URS-001? / show mapping for URS-003 / which documents are missing?")

    def find_item_by_code(code: str):
        code = code.upper().replace("_", "-").replace(" ", "-")
        for item in st.session_state["items"]:
            if item.get("item_code", "").upper() == code:
                return item
        return None

    def find_matrix_by_urs(code: str):
        code = code.upper().replace("_", "-").replace(" ", "-")
        for row in st.session_state["matrix"]:
            if row.get("URS ID", "").upper() == code:
                return row
        return None

    if st.button("Ask Agent", type="primary"):
        ql = q.lower().strip()
        id_match = re.search(r"\b(URS|FRS|FS|DS|IQ|OQ|PQ|SOP)[-_ ]?(\d{1,4})\b", q, re.I)

        if id_match:
            prefix = id_match.group(1).upper()
            if prefix == "FS":
                prefix = "FRS"
            code = f"{prefix}-{int(id_match.group(2)):03d}"

            item = find_item_by_code(code)
            urs_row = find_matrix_by_urs(code) if prefix == "URS" else None

            if "map" in ql or "trace" in ql or "downstream" in ql or prefix == "URS":
                if prefix == "URS" and urs_row:
                    st.success(f"Traceability found for {code}")
                    st.dataframe(pd.DataFrame([urs_row]), use_container_width=True)
                    st.markdown("**Downstream path:**")
                    st.write(f"{urs_row.get('URS ID')} → {urs_row.get('FRS ID')} → {urs_row.get('DS ID')} → {urs_row.get('IQ ID')} → {urs_row.get('OQ ID')} → {urs_row.get('PQ ID')}")
                elif item:
                    st.success(f"Item found: {code}")
                    st.json(item)
                    related_urs = item.get("related_urs")
                    if related_urs:
                        row = find_matrix_by_urs(related_urs)
                        if row:
                            st.markdown(f"**Related URS mapping for {related_urs}:**")
                            st.dataframe(pd.DataFrame([row]), use_container_width=True)
                else:
                    st.warning(f"I could not find {code} in the extracted items or matrix.")
            else:
                if item:
                    st.success(f"Definition found for {code}")
                    st.markdown(f"**{item.get('item_code')} - {item.get('title', '')}**")
                    st.write(item.get("item_text", ""))
                    st.caption(f"Type: {item.get('item_type')} | Source: {item.get('document_name')} | Source Ref: {item.get('source_ref')} | ID Source: {item.get('id_source')}")
                else:
                    st.warning(f"I could not find {code}. Please check extracted items.")

        elif "gap" in ql or "missing" in ql:
            gaps = st.session_state["gaps"]
            if gaps:
                st.write("These gaps are currently available:")
                st.dataframe(pd.DataFrame(gaps), use_container_width=True)
            else:
                st.success("No gaps are currently found.")

        elif "reject" in ql or "invalid" in ql:
            rejected = [d for d in st.session_state["documents"] if not d.get("is_valid")]
            if rejected:
                st.write("Rejected/invalid documents:")
                st.dataframe(pd.DataFrame(rejected), use_container_width=True)
            else:
                st.success("No rejected documents are currently found.")

        elif "auto" in ql:
            auto = [i for i in st.session_state["items"] if i.get("id_source") == "AUTO_GENERATED"]
            if auto:
                st.write("Auto-generated items requiring review:")
                st.dataframe(pd.DataFrame(auto), use_container_width=True)
            else:
                st.success("No auto-generated IDs are currently found.")

        elif "partial" in ql:
            partial = [r for r in st.session_state["matrix"] if r.get("Status") == "Partial"]
            if partial:
                st.write("Partial traceability rows:")
                st.dataframe(pd.DataFrame(partial), use_container_width=True)
            else:
                st.success("No partial rows are currently found.")

        elif "complete" in ql:
            complete = [r for r in st.session_state["matrix"] if r.get("Status") == "Complete"]
            st.write(f"Complete traceability rows: {len(complete)}")
            st.dataframe(pd.DataFrame(complete), use_container_width=True)

        elif "summary" in ql or "status" in ql:
            st.write({
                "valid_documents": len([d for d in st.session_state["documents"] if d.get("is_valid")]),
                "rejected_documents": len([d for d in st.session_state["documents"] if not d.get("is_valid")]),
                "extracted_items": len(st.session_state["items"]),
                "matrix_rows": len(st.session_state["matrix"]),
                "gaps": len(st.session_state["gaps"]),
            })

        else:
            st.write("I can answer questions like: what is URS-001, show mapping for URS-003, which documents are missing, show gaps, show rejected files, show auto-generated IDs, and show complete/partial mappings.")
