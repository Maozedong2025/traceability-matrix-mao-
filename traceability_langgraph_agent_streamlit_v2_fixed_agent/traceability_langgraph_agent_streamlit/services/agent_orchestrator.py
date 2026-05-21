from typing import TypedDict, List, Dict, Any
from services.agent_tools import file_type_detector_tool, invalid_document_checker_tool, document_classifier_tool, item_extractor_tool, mapping_tool, gap_tool

try:
    from langgraph.graph import StateGraph, END
    LANGGRAPH_AVAILABLE = True
except Exception:
    LANGGRAPH_AVAILABLE = False

class TraceabilityState(TypedDict, total=False):
    documents: List[Dict[str, Any]]
    items: List[Dict[str, Any]]
    matrix: List[Dict[str, Any]]
    forward: List[Dict[str, Any]]
    downstream: List[Dict[str, Any]]
    gaps: List[Dict[str, Any]]
    messages: List[str]

def check_uploaded_files_node(state):
    msgs = state.get("messages", [])
    for doc in state.get("documents", []):
        doc["file_type_info"] = file_type_detector_tool(doc["file_name"])
    msgs.append(f"Agent checked {len(state.get('documents', []))} uploaded file(s).")
    state["messages"] = msgs
    return state

def validate_and_classify_node(state):
    msgs = state.get("messages", [])
    for doc in state.get("documents", []):
        if not doc.get("file_type_info", {}).get("is_supported"):
            doc.update({"is_valid":False, "predicted_category":"NOT_VALIDATION_DOCUMENT", "confirmed_category":"NOT_VALIDATION_DOCUMENT", "rejection_reason":"Unsupported file type."})
            continue
        check = invalid_document_checker_tool(doc["file_name"], doc.get("full_text",""))
        doc["validation_check"] = check
        doc["is_valid"] = check.get("is_valid", False)
        if not doc["is_valid"]:
            doc.update({"predicted_category":"NOT_VALIDATION_DOCUMENT", "confirmed_category":"NOT_VALIDATION_DOCUMENT", "rejection_reason":check.get("reason","Invalid document.")})
        else:
            cls = document_classifier_tool(doc["file_name"], doc.get("full_text",""))
            doc.update({"predicted_category":cls["document_type"], "confirmed_category":cls["document_type"], "classification_reason":cls["reason"]})
    valid = len([d for d in state.get("documents", []) if d.get("is_valid")])
    msgs.append(f"Agent validated documents. Valid: {valid}, Rejected: {len(state.get('documents', [])) - valid}.")
    state["messages"] = msgs
    return state

def extract_items_node(state):
    items = []
    for doc in state.get("documents", []):
        if doc.get("is_valid"):
            items.extend(item_extractor_tool(doc.get("full_text",""), doc.get("confirmed_category",""), doc.get("file_name",""), doc.get("chunks", [])))
    state["items"] = items
    state.setdefault("messages", []).append(f"Agent extracted {len(items)} item(s).")
    return state

def mapping_node(state):
    matrix, forward, downstream = mapping_tool(state.get("items", []))
    state["matrix"], state["forward"], state["downstream"] = matrix, forward, downstream
    state.setdefault("messages", []).append(f"Agent generated {len(matrix)} traceability row(s).")
    return state

def gap_node(state):
    state["gaps"] = gap_tool(state.get("documents", []), state.get("matrix", []), state.get("items", []))
    state.setdefault("messages", []).append(f"Agent identified {len(state['gaps'])} gap/review item(s).")
    return state

def build_graph():
    if not LANGGRAPH_AVAILABLE:
        return None
    graph = StateGraph(TraceabilityState)
    graph.add_node("check_uploaded_files", check_uploaded_files_node)
    graph.add_node("validate_and_classify", validate_and_classify_node)
    graph.add_node("extract_items", extract_items_node)
    graph.add_node("map_traceability", mapping_node)
    graph.add_node("find_gaps", gap_node)
    graph.set_entry_point("check_uploaded_files")
    graph.add_edge("check_uploaded_files", "validate_and_classify")
    graph.add_edge("validate_and_classify", "extract_items")
    graph.add_edge("extract_items", "map_traceability")
    graph.add_edge("map_traceability", "find_gaps")
    graph.add_edge("find_gaps", END)
    return graph.compile()

def run_agent_pipeline(documents):
    initial = {"documents": documents, "messages": []}
    graph = build_graph()
    if graph:
        return graph.invoke(initial)
    state = initial
    for node in [check_uploaded_files_node, validate_and_classify_node, extract_items_node, mapping_node, gap_node]:
        state = node(state)
    state.setdefault("messages", []).append("LangGraph unavailable. Used sequential fallback orchestrator.")
    return state
