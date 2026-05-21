import re
from services.text_cleaner import split_meaningful_blocks
from services.auto_id_generator import AutoIdGenerator

def normalize_code(prefix, num):
    return f"{prefix.upper()}-{int(num):03d}"

def contains_ids_for_category(text, category):
    cat = "FRS|FS" if category in ["FRS","FS"] else category
    return re.search(rf"\b({cat})[-_ ]?\d{{1,4}}\b", text, re.I) is not None

def find_related(text, target):
    if target == "URS":
        m = re.search(r"\bURS[-_ ]?(\d{1,4})\b", text, re.I)
        return normalize_code("URS", m.group(1)) if m else ""
    if target == "FRS":
        m = re.search(r"\b(FRS|FS)[-_ ]?(\d{1,4})\b", text, re.I)
        return normalize_code("FRS", m.group(2)) if m else ""
    return ""

def extract_structured_items(text, category, document_name, chunks):
    items = []
    pattern_cat = "FRS|FS" if category in ["FRS","FS"] else category
    pat = re.compile(rf"\b({pattern_cat})[-_ ]?(\d{{1,4}})\b", re.I)
    for chunk in chunks:
        t = chunk.get("text","")
        for m in pat.finditer(t):
            prefix = "FRS" if m.group(1).upper() == "FS" else m.group(1).upper()
            code = normalize_code(prefix, m.group(2))
            context = t[max(0,m.start()-150):min(len(t),m.end()+650)].strip()
            if any(x["item_code"] == code and x["document_name"] == document_name for x in items):
                continue
            items.append({
                "item_code": code, "item_type": "FRS" if category=="FS" else category,
                "title": context[:120], "item_text": context,
                "related_urs": code if category=="URS" else find_related(context, "URS"),
                "related_frs": code if category in ["FRS","FS"] else find_related(context, "FRS"),
                "document_name": document_name, "source_ref": chunk.get("source_ref",""),
                "id_source": "ORIGINAL", "confidence": "High", "review_required": False
            })
    return items

def terms_for(category):
    return {
        "URS":["shall","should","must","user shall","system shall","system should"],
        "FRS":["shall provide","shall display","shall validate","workflow","functional","business rule"],
        "FS":["shall provide","shall display","shall validate","workflow","functional","business rule"],
        "DS":["configure","configuration","database","api","object","field","role","permission","workflow"],
        "IQ":["verify installation","verify version","url","environment","installed","deployed","configuration available"],
        "OQ":["verify","test","expected result","pass","fail","function"],
        "PQ":["business process","end-to-end","scenario","realistic","production-like","perform"],
        "SOP":["procedure","responsibility","shall","review","approval"]
    }.get(category, [])

def extract_messy_items(text, category, document_name):
    g = AutoIdGenerator()
    blocks = split_meaningful_blocks(text)
    items = []
    for block in blocks:
        lb = block.lower()
        if any(term in lb for term in terms_for(category)):
            cat = "FRS" if category=="FS" else category
            items.append({
                "item_code": g.next_id(cat), "item_type": cat, "title": block[:100],
                "item_text": block, "related_urs": find_related(block, "URS"),
                "related_frs": find_related(block, "FRS"), "document_name": document_name,
                "source_ref": "Auto extracted messy text", "id_source": "AUTO_GENERATED",
                "confidence": "Medium", "review_required": True
            })
    return items

def extract_items(text, confirmed_category, document_name, chunks):
    if confirmed_category in ["UNKNOWN","NOT_VALIDATION_DOCUMENT",""]:
        return []
    category = "FRS" if confirmed_category=="FS" else confirmed_category
    if contains_ids_for_category(text, category):
        found = extract_structured_items(text, category, document_name, chunks)
        if found:
            return found
    return extract_messy_items(text, category, document_name)
