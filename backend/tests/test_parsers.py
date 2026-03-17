import pytest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from parsers import parse_document
from models import DocumentORM

def make_doc(source_type: str, **kwargs) -> DocumentORM:
    d = DocumentORM()
    d.id = "test-id"
    d.source_type = source_type
    d.filename = kwargs.get("filename", "test")
    d.file_path = kwargs.get("file_path")
    d.source_url = kwargs.get("source_url")
    d.extracted_text = ""
    d.metadata_json = "{}"
    return d

def test_text_parser_returns_text():
    doc = make_doc("text", filename="notes.txt")
    result = parse_document(doc, raw_content="hello world")
    assert "hello world" in result

def test_markdown_parser_strips_formatting():
    doc = make_doc("markdown", filename="README.md")
    result = parse_document(doc, raw_content="# Title\n**bold** text")
    assert "Title" in result
    assert "bold" in result

def test_url_parser_needs_url():
    doc = make_doc("url", source_url=None)
    with pytest.raises(ValueError, match="source_url"):
        parse_document(doc)

def test_unknown_source_type_raises():
    doc = make_doc("unknown")
    with pytest.raises(ValueError, match="Unknown source_type"):
        parse_document(doc)
