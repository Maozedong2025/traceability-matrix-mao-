from services.file_utils import detect_file_type
from services.validation_document_checker import check_validation_document
from services.classifier import classify_document
from services.item_extractor import extract_items
from services.mapping_engine import generate_traceability_matrix, generate_forward_mapping, generate_downstream_mapping
from services.gap_analyzer import generate_gap_report

def file_type_detector_tool(file_name):
    return detect_file_type(file_name)
def invalid_document_checker_tool(file_name, text):
    return check_validation_document(file_name, text)
def document_classifier_tool(file_name, text):
    return classify_document(file_name, text)
def item_extractor_tool(text, category, document_name, chunks):
    return extract_items(text, category, document_name, chunks)
def mapping_tool(items):
    matrix = generate_traceability_matrix(items)
    return matrix, generate_forward_mapping(matrix), generate_downstream_mapping(matrix)
def gap_tool(documents, matrix, items):
    return generate_gap_report(documents, matrix, items)
