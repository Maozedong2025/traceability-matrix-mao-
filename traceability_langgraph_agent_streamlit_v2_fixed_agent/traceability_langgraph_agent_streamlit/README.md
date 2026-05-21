# AI-Assisted Traceability Matrix Generator with LangGraph Agent

This Streamlit project uses a LangGraph-style agent orchestrator to generate an AI-assisted draft traceability matrix from URS, FRS/FS, DS, IQ, OQ, PQ, and SOP documents.

## Workflow
User uploads documents -> Agent checks files -> Detect file type -> Extract text -> Validate document -> Classify category -> User confirms category -> Extract structured/messy items -> Auto-generate IDs when needed -> RAG-style mapping -> Generate matrix -> Find gaps -> User review -> Export Excel.

## Run
```bash
cd traceability_langgraph_agent_streamlit
python -m venv venv
venv\Scripts\activate
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

Compliance note: AI/RAG output is draft only. QA/Validation review is required before official industrial or life-science use.
