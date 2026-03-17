import pytest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.chat_service import parse_action_from_response, detect_intent

def test_parse_action_section_update():
    response = 'Here is the updated section.\n<ACTION>\n{"action": "section_update", "section_id": "overview", "html": "<section>...</section>"}\n</ACTION>'
    text, action = parse_action_from_response(response)
    assert text.strip() == "Here is the updated section."
    assert action["action"] == "section_update"
    assert action["section_id"] == "overview"

def test_parse_action_none_when_absent():
    response = "The auth service uses JWT tokens with a 1-hour TTL."
    text, action = parse_action_from_response(response)
    assert text == response
    assert action is None

def test_detect_intent_edit():
    assert detect_intent("add a sequence diagram for login") == "edit"
    assert detect_intent("insert a risk about database failures") == "edit"
    assert detect_intent("update the overview section") == "edit"

def test_detect_intent_qa():
    assert detect_intent("what is the main architecture pattern?") == "qa"
    assert detect_intent("explain the data flow") == "qa"
    assert detect_intent("summarize the key risks") == "qa"

def test_detect_intent_new_report():
    assert detect_intent("compare these docs and draft a new proposal") == "new_report"
    assert detect_intent("generate a new architecture proposal") == "new_report"
