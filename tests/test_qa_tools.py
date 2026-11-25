"""Exercise the QA boundary: source mutation, analyzer evidence, exact review."""
import json
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools" / "ci"))
from audit_cppcheck import summarize
from review_gate import review_state, TRUSTED_LOGIN, TRUSTED_USER
from mutation_transport import mutate


def test_mutation_replaces_unique_anchor_only():
    assert mutate("abc", None, "b", "B") == "aBc"
    with pytest.raises(ValueError):
        mutate("bb", None, "b", "B")


def test_audit_requires_complete_file_inventory():
    xml = '<results><errors><error severity="warning"/></errors></results>'
    assert summarize(xml, "2/2 files checked", 2) == {"warning": 1}
    with pytest.raises(ValueError):
        summarize(xml, "1/2 files checked", 2)


def receipt(head, status="completed", unresolved=False, user_id=TRUSTED_USER):
    return {
        "user": {"id": user_id, "login": TRUSTED_LOGIN, "type": "Bot"},
        "body": "<!-- codex-review-state:v1 " + json.dumps({
            "code_review": {"commit_sha": head, "status": status,
                            "has_unresolved_findings": unresolved}
        }) + " -->",
    }


def test_review_exact_head_only():
    assert review_state([[receipt("a")]], "a") == "clean"
    assert review_state([[receipt("a")]], "b") == "missing"
    assert review_state([[receipt("a", user_id=1)]], "a") == "missing"


def test_review_rejects_findings_and_unknown():
    assert review_state([[receipt("a", unresolved=True)]], "a") == "findings"
    assert review_state([[receipt("a", unresolved=None)]], "a") == "unknown"
    assert review_state([[receipt("a"), receipt("a", "running")]], "a") == "running"
