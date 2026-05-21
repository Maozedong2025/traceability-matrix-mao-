from pathlib import Path
APP_TITLE = "AI-Assisted Traceability Matrix Generator"
APP_SUBTITLE = "LangGraph Agent Workflow for URS, FRS/FS, DS, IQ, OQ, PQ and SOP"
ACCEPTED_EXTENSIONS = [".pdf", ".docx", ".xlsx", ".xls", ".csv", ".txt"]
VALIDATION_CATEGORIES = ["URS", "FRS", "FS", "DS", "IQ", "OQ", "PQ", "SOP"]
REQUIRED_MATRIX_CATEGORIES = ["URS", "FRS", "DS", "IQ", "OQ", "PQ"]
UPLOAD_DIR = Path("uploads")
EXPORT_DIR = Path("exports")
UPLOAD_DIR.mkdir(exist_ok=True)
EXPORT_DIR.mkdir(exist_ok=True)
