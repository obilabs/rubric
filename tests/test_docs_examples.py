"""The questions embedded in the renderer docs must still parse.

`docs/BUILD-A-RENDERER.md` and `web/renderer-example.html` both inline a Rubric
question as a JavaScript array of string literals. That example is the first
thing a stranger copies, so it does not get to rot silently when the format
moves: the reference parser checks it here, and the conformance corpus keeps the
JavaScript parser in step with the reference.
"""

import json
import os
import re

import pytest

from rubric import validate_dsl

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOC = os.path.join(REPO_ROOT, "docs", "BUILD-A-RENDERER.md")
EXAMPLE = os.path.join(REPO_ROOT, "web", "renderer-example.html")

# A `[ "line", "line", ].join("\n")` block — how both files embed a question.
_ARRAY = re.compile(r'\[\s*\n(?P<body>(?:\s*"(?:[^"\\]|\\.)*",?\s*\n)+)\s*\]\.join\("\\n"\)')
_STRING = re.compile(r'^\s*("(?:[^"\\]|\\.)*"),?\s*$', re.M)


def embedded_questions(path):
    """Every inlined DSL document in a source file, as text."""
    with open(path, "r", encoding="utf-8") as fh:
        source = fh.read()
    out = []
    for block in _ARRAY.finditer(source):
        lines = [json.loads(m.group(1)) for m in _STRING.finditer(block.group("body"))]
        out.append("\n".join(lines))
    return out


@pytest.mark.parametrize("path", [DOC, EXAMPLE], ids=["build-a-renderer", "renderer-example"])
def test_embedded_questions_parse(path):
    questions = embedded_questions(path)
    assert questions, f"no embedded question found in {os.path.basename(path)}"
    for dsl in questions:
        result = validate_dsl(dsl)
        assert result.success, [e.message for e in result.errors]


def test_the_doc_example_actually_carries_a_rationale():
    """The page exists to show the per-choice rationale — it must have one."""
    for dsl in embedded_questions(DOC):
        data = validate_dsl(dsl).data
        if data["choices"]:
            assert any(c["rationale"] for c in data["choices"])


def test_renderer_example_exercises_the_unsupported_type_branch():
    """The shipped page shows both a handled and an unhandled type."""
    types = {validate_dsl(dsl).data["type"] for dsl in embedded_questions(EXAMPLE)}
    assert "SINGLE_CHOICE" in types
    assert types - {"SINGLE_CHOICE", "MULTIPLE_CHOICE", "TRUE_FALSE"}, (
        "the example should also carry a type its renderer does not handle"
    )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
