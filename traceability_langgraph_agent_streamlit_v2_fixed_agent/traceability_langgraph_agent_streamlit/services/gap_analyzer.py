from config import REQUIRED_MATRIX_CATEGORIES

def missing_document_gaps(documents):
    present = {d.get("confirmed_category") for d in documents if d.get("is_valid")}
    gaps = []
    for req in REQUIRED_MATRIX_CATEGORIES:
        if req == "FRS":
            if "FRS" not in present and "FS" not in present:
                gaps.append({"Gap Type":"Missing Document","Related ID":"FRS/FS","Description":"FRS/FS document is missing.","Risk":"High"})
        elif req not in present:
            gaps.append({"Gap Type":"Missing Document","Related ID":req,"Description":f"{req} document is missing.","Risk":"High"})
    return gaps

def mapping_gaps(matrix_rows):
    gaps = []
    for row in matrix_rows:
        for target in ["FRS","DS","IQ","OQ","PQ"]:
            if row.get(f"{target} ID") == "Missing":
                gaps.append({"Gap Type":f"Missing {target} Mapping","Related ID":row.get("URS ID"),"Description":f"{row.get('URS ID')} has no mapped {target} item.","Risk":"High" if target in ["FRS","OQ","PQ"] else "Medium"})
        if row.get("Confidence") == "Low":
            gaps.append({"Gap Type":"Low Confidence Mapping","Related ID":row.get("URS ID"),"Description":f"{row.get('URS ID')} has low confidence mapping.","Risk":"Medium"})
    return gaps

def review_gaps(items):
    return [{"Gap Type":"Review Required","Related ID":i.get("item_code"),"Description":"Auto-generated ID or messy extraction requires user review.","Risk":"Medium"} for i in items if i.get("review_required")]

def generate_gap_report(documents, matrix_rows, items):
    return missing_document_gaps(documents) + mapping_gaps(matrix_rows) + review_gaps(items)
