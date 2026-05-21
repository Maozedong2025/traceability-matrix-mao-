from io import BytesIO
import pandas as pd

def as_df(data):
    return pd.DataFrame(data) if data else pd.DataFrame()

def export_excel(summary, matrix, forward, downstream, gaps, docs, items):
    output = BytesIO()
    safe_docs = []
    for d in docs:
        safe_docs.append({
            "file_name": d.get("file_name"), "is_valid": d.get("is_valid"),
            "predicted_category": d.get("predicted_category"), "confirmed_category": d.get("confirmed_category"),
            "reason": d.get("classification_reason") or d.get("rejection_reason") or d.get("validation_check",{}).get("reason","")
        })
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        as_df(summary).to_excel(writer, "Summary", index=False)
        as_df(matrix).to_excel(writer, "Traceability Matrix", index=False)
        as_df(forward).to_excel(writer, "Forward Mapping", index=False)
        as_df(downstream).to_excel(writer, "Downstream Mapping", index=False)
        as_df(gaps).to_excel(writer, "Gap Analysis", index=False)
        as_df(safe_docs).to_excel(writer, "Document Inventory", index=False)
        as_df(items).to_excel(writer, "Extracted Items", index=False)
        for ws in writer.book.worksheets:
            ws.freeze_panes = "A2"
            for col in ws.columns:
                letter = col[0].column_letter
                max_len = min(max([len(str(c.value)) if c.value is not None else 0 for c in col] + [12]), 80)
                ws.column_dimensions[letter].width = max_len + 2
    return output.getvalue()
