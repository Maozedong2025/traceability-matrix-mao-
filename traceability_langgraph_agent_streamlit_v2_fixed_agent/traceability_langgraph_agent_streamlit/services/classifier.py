import re
SIGNALS = {
    "URS":["user requirement specification","user requirements specification","the system shall","business requirement","user shall","system should"],
    "FRS":["functional requirement specification","functional requirements specification","functional requirement","functional behavior","business rule"],
    "FS":["functional specification","functional design"],
    "DS":["design specification","technical design","configuration design","configure","object fields","permission set","workflow configuration"],
    "IQ":["installation qualification","iq protocol","verify installation","environment","url accessible","version installed","deployed"],
    "OQ":["operational qualification","oq protocol","test step","expected result","actual result","pass/fail","verify function"],
    "PQ":["performance qualification","pq protocol","business process","end-to-end","realistic user scenario","production-like"],
    "SOP":["standard operating procedure","purpose:","scope:","responsibilities:","procedure:","revision history"],
}
def classify_document(file_name: str, text: str) -> dict:
    content = (file_name + "\n" + text[:15000]).lower()
    scores = {k:0 for k in SIGNALS}
    lname = file_name.lower()
    for cat in scores:
        if re.search(rf"\b{cat.lower()}\b|_{cat.lower()}_|-{cat.lower()}-", lname):
            scores[cat] += 5
    for cat, terms in SIGNALS.items():
        for term in terms:
            if term in content:
                scores[cat] += 2
    for cat in scores:
        if re.search(rf"\b{cat}[-_ ]?\d{{1,4}}\b", content, re.I):
            scores[cat] += 5
    if "installation qualification" in content: scores["IQ"] += 8
    if "operational qualification" in content: scores["OQ"] += 8
    if "performance qualification" in content: scores["PQ"] += 8
    best = max(scores, key=scores.get)
    score = scores[best]
    if score < 4:
        return {"document_type": "UNKNOWN", "confidence": 0.0, "reason": "Not enough category evidence."}
    return {"document_type": best, "confidence": min(score/16, 1.0), "reason": f"Detected {best} using title, keyword and ID-pattern evidence."}
