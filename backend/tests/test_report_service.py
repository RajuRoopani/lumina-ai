import pytest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from unittest.mock import patch, MagicMock
from services.report_service import generate_report_html, pick_signature_color
from models import DocumentORM


def make_doc(text: str) -> DocumentORM:
    d = DocumentORM()
    d.id = "doc-1"
    d.filename = "test.md"
    d.source_type = "text"
    d.extracted_text = text
    d.metadata_json = "{}"
    return d


def test_pick_signature_color_cycles():
    colors = [pick_signature_color(i) for i in range(6)]
    assert len(set(colors)) == 6  # all 6 are distinct
    assert pick_signature_color(6) == pick_signature_color(0)  # wraps


def test_generate_report_html_returns_html():
    mock_client = MagicMock()
    mock_client.messages.create.return_value = MagicMock(
        content=[MagicMock(text="<!DOCTYPE html><html><body>Test Report</body></html>")]
    )
    with patch("services.report_service.anthropic.Anthropic", return_value=mock_client):
        result = generate_report_html([make_doc("Sample document text")], signature_color="#388bfd")
    assert "<!DOCTYPE html>" in result
    mock_client.messages.create.assert_called_once()


def test_generate_report_raises_on_empty_docs():
    with pytest.raises(ValueError, match="at least one document"):
        generate_report_html([], signature_color="#388bfd")
