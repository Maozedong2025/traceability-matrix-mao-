import re
VALIDATION_TERMS = [
    "user requirement specification","user requirements specification","functional requirement specification",
    "functional specification","design specification","installation qualification","operational qualification",
    "performance qualification","standard operating procedure","validation","qualification","traceability",
    "test case","expected result"
]
NON_VALIDATION_HINTS = [
    "hcp name","npi number","territory","brand","call notes","prescriber","doctor","samples left",
    "rep name","deviation classification","training data","final classification"
]
ID_PATTERN = re.compile(r"\b(URS|FRS|FS|DS|IQ|OQ|PQ|SOP)[-_ ]?\d{1,4}\b", re.I)

def check_validation_document(file_name: str, text: str) -> dict:
    content = (file_name + "\n" + text[:12000]).lower()
    non_hits = [h for h in NON_VALIDATION_HINTS if h in content]
    val_hits = [t for t in VALIDATION_TERMS if t in content]
    ids = ID_PATTERN.findall(content)
    if len(non_hits) >= 2 and len(val_hits) < 2 and len(ids) < 3:
        return {"is_valid": False, "reason": "This appears to be business/training/data content, not a validation lifecycle document.", "evidence": ", ".join(non_hits[:5])}
    if val_hits or len(ids) >= 2:
        return {"is_valid": True, "reason": "Validation lifecycle indicators found.", "evidence": ", ".join(val_hits[:5]) or f"{len(ids)} validation IDs found"}
    messy_hits = [p for p in ["the system shall","system should","verify that","expected result","configure","audit trail","electronic signature","role based","role-based"] if p in content]
    if len(messy_hits) >= 2:
        return {"is_valid": True, "reason": "Messy validation-style content found.", "evidence": ", ".join(messy_hits[:5])}
    return {"is_valid": False, "reason": "No strong validation lifecycle evidence found.", "evidence": ""}
