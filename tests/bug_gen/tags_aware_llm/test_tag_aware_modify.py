import pytest
from types import SimpleNamespace

from swesmith.bug_gen.tags_aware_llm.tag_aware_modify import (
    _build_tag_bug_types,
    TAG_PRIORITY_KEYS,
)


def test_build_tag_bug_types_respects_priority_and_limit():
    candidate = SimpleNamespace(
        has_if=True,
        has_loop=True,
        has_exception=True,
        has_return=True,
    )

    tag_to_bug_type = {
        "HAS_IF": "IF bug",
        "HAS_LOOP": "LOOP bug",
        "HAS_EXCEPTION": "EXCEPTION bug",
        "HAS_RETURN": "RETURN bug",
    }

    result = _build_tag_bug_types(
        candidate,
        tag_to_bug_type,
        max_tag_bug_types=2,
    )

    lines = result.split("\n")

    # Should respect priority order from TAG_PRIORITY_KEYS
    assert lines == [
        "- LOOP bug",
        "- IF bug",
    ]


def test_build_tag_bug_types_returns_default_when_no_match():
    candidate = SimpleNamespace()

    result = _build_tag_bug_types(
        candidate,
        tag_to_bug_type={},
        max_tag_bug_types=3,
    )

    assert "Introduce a subtle logical bug" in result
