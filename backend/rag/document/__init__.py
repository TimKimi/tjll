"""文档加载 / 清洗 / 切分 / 入库。"""

from backend.rag.document.chunking import split_text_to_chunks
from backend.rag.document.clean import clean_text
from backend.rag.document.indexing import index_file_to_opensearch
from backend.rag.document.loaders import load_document_as_text
from backend.rag.document.pdf import parse_pdf_with_mineru

__all__ = [
    "clean_text",
    "index_file_to_opensearch",
    "load_document_as_text",
    "parse_pdf_with_mineru",
    "split_text_to_chunks",
]
