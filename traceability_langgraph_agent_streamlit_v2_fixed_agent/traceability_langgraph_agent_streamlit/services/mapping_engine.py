from services.rag_engine import retrieve_similar

def by_type(items, t):
    return [i for i in items if i.get("item_type") == t]

def find_related_urs(items, urs):
    for i in items:
        if i.get("related_urs") == urs:
            return i.copy()
    return {}

def find_related_frs(items, frs):
    for i in items:
        if frs and i.get("related_frs") == frs:
            return i.copy()
    return {}

def best_match(urs_item, candidates, target_type, frs_code=""):
    exact = find_related_urs(candidates, urs_item["item_code"])
    if exact:
        exact["match_type"], exact["match_confidence"] = "EXACT_RELATED_URS", "High"
        return exact
    if target_type == "DS" and frs_code:
        byfrs = find_related_frs(candidates, frs_code)
        if byfrs:
            byfrs["match_type"], byfrs["match_confidence"] = "EXACT_RELATED_FRS", "High"
            return byfrs
    rag = retrieve_similar(urs_item.get("item_text",""), candidates, 1)
    if rag and rag[0].get("rag_score",0) >= 0.18:
        r = rag[0]
        r["match_type"] = "RAG_SIMILARITY"
        r["match_confidence"] = "Medium" if r["rag_score"] >= 0.30 else "Low"
        return r
    return {}

def generate_traceability_matrix(items):
    rows = []
    for urs in by_type(items, "URS"):
        frs = best_match(urs, by_type(items,"FRS"), "FRS")
        ds = best_match(urs, by_type(items,"DS"), "DS", frs.get("item_code",""))
        iq = best_match(urs, by_type(items,"IQ"), "IQ")
        oq = best_match(urs, by_type(items,"OQ"), "OQ")
        pq = best_match(urs, by_type(items,"PQ"), "PQ")
        pairs = [("FRS",frs),("DS",ds),("IQ",iq),("OQ",oq),("PQ",pq)]
        missing = [k for k,v in pairs if not v]
        status = "Complete" if not missing else ("Missing" if len(missing)==5 else "Partial")
        confs = [v.get("match_confidence") for _,v in pairs if v]
        overall = "High" if confs and all(c=="High" for c in confs) else ("Medium" if confs else "Low")
        row = {"URS ID": urs["item_code"], "URS Content": urs.get("item_text","")}
        for k,v in pairs:
            row[f"{k} ID"] = v.get("item_code","Missing") if v else "Missing"
            row[f"{k} Content"] = v.get("item_text","") if v else ""
        row.update({
            "Status": status, "Confidence": overall,
            "Remarks": "All required mappings found." if not missing else "Missing: " + ", ".join(missing),
            "Evidence": " | ".join([v.get("rag_reason") or v.get("match_type","") for _,v in pairs if v])
        })
        rows.append(row)
    return rows

def generate_forward_mapping(matrix_rows):
    out = []
    for row in matrix_rows:
        for target in ["FRS","DS","IQ","OQ","PQ"]:
            out.append({
                "Source ID": row["URS ID"], "Source Content": row["URS Content"],
                "Target Type": target, "Target ID": row.get(f"{target} ID","Missing"),
                "Target Content": row.get(f"{target} Content",""),
                "Mapping With Content": f'{row["URS ID"]}: {row["URS Content"]} → {row.get(f"{target} ID","Missing")}: {row.get(f"{target} Content","")}'
            })
    return out

def generate_downstream_mapping(matrix_rows):
    out = []
    for row in matrix_rows:
        id_path = f'{row["URS ID"]} → {row["FRS ID"]} → {row["DS ID"]} → {row["IQ ID"]} → {row["OQ ID"]} → {row["PQ ID"]}'
        content_path = f'{row["URS ID"]}: {row["URS Content"]}\n→ {row["FRS ID"]}: {row["FRS Content"]}\n→ {row["DS ID"]}: {row["DS Content"]}\n→ {row["IQ ID"]}: {row["IQ Content"]}\n→ {row["OQ ID"]}: {row["OQ Content"]}\n→ {row["PQ ID"]}: {row["PQ Content"]}'
        out.append({"URS ID": row["URS ID"], "Downstream ID Path": id_path, "Downstream Content Path": content_path, "Status": row["Status"]})
    return out
