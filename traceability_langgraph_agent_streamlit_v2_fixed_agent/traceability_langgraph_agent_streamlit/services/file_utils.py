from pathlib import Path
import re
from config import ACCEPTED_EXTENSIONS, UPLOAD_DIR

def safe_filename(name: str) -> str:
    return re.sub(r"[^a-zA-Z0-9_. -]", "_", name).strip().replace(" ", "_")

def detect_file_type(file_name: str) -> dict:
    ext = Path(file_name).suffix.lower()
    return {
        "extension": ext,
        "is_supported": ext in ACCEPTED_EXTENSIONS,
        "file_type": {".pdf":"PDF",".docx":"Word",".xlsx":"Excel",".xls":"Excel",".csv":"CSV",".txt":"Text"}.get(ext, "Unsupported")
    }

def save_uploaded_file(uploaded_file) -> str:
    name = safe_filename(uploaded_file.name)
    path = UPLOAD_DIR / name
    with open(path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    return str(path)
