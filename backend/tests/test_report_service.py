import pytest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from unittest.mock import patch, MagicMock, call
from services.report_service import generate_report_html, pick_signature_color, build_document_context
from models import DocumentORM


def make_doc(text: str, filename: str = "test.md") -> DocumentORM:
    d = DocumentORM()
    d.id = "doc-1"
    d.filename = filename
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
    mock_response = MagicMock()
    mock_response.content = [MagicMock(text="<!DOCTYPE html><html><body>Test Report</body></html>")]
    mock_client.messages.create.return_value = mock_response

    with patch("services.report_service.anthropic.Anthropic", return_value=mock_client), \
         patch("services.report_service.ANTHROPIC_API_KEY", "test-key"):
        result = generate_report_html([make_doc("Sample document text")], signature_color="#388bfd")

    assert "<!DOCTYPE html>" in result
    call_kwargs = mock_client.messages.create.call_args
    assert call_kwargs.kwargs["model"] == "claude-sonnet-4-6"
    assert call_kwargs.kwargs["max_tokens"] == 8192
    assert "{SIGNATURE_COLOR}" not in call_kwargs.kwargs["system"]  # substituted
    assert "388bfd" in call_kwargs.kwargs["system"]


def test_generate_report_raises_on_empty_docs():
    with pytest.raises(ValueError, match="at least one document"):
        generate_report_html([], signature_color="#388bfd")


def test_generate_report_multi_doc_includes_comparison_instruction():
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.content = [MagicMock(text="<!DOCTYPE html><html><body>Multi Report</body></html>")]
    mock_client.messages.create.return_value = mock_response

    with patch("services.report_service.anthropic.Anthropic", return_value=mock_client), \
         patch("services.report_service.ANTHROPIC_API_KEY", "test-key"):
        result = generate_report_html(
            [make_doc("doc one text", "one.pdf"), make_doc("doc two text", "two.pdf")],
            signature_color="#3fb950"
        )

    assert "<!DOCTYPE html>" in result
    user_content = mock_client.messages.create.call_args.kwargs["messages"][0]["content"]
    assert "MULTI-DOCUMENT" in user_content
    assert "per-doc-analysis" in user_content
    assert "comparison" in user_content
    assert "synthesis" in user_content


def test_build_document_context_truncates_long_text():
    long_text = "x" * 7000
    doc = make_doc(long_text, "big.pdf")
    context = build_document_context([doc])
    assert "[truncated]" in context
    # Should not contain the full 7000 chars
    assert len(context) < 7000
