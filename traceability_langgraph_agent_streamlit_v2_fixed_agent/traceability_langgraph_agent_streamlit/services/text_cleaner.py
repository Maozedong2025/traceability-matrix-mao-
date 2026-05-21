import re

def clean_text(text: str) -> str:
    text = text.replace("\x00", " ")
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"(?i)(the system shall|system shall|system should|verify that|verify|configure|expected result)", r"\n\1", text)
    return text.strip()

def split_meaningful_blocks(text: str):
    text = clean_text(text)
    parts = re.split(r"\n|(?<=[.;])\s+", text)
    return [p.strip(" -•\t") for p in parts if len(p.split()) >= 4]
