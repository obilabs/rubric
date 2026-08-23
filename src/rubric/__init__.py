"""
Rubric — an open, git-native format for exam-prep question banks.

A question is a Markdown file: YAML frontmatter for metadata, Markdown body for
the prompt and choices. The correct choice is marked ``*[CORRECT]*``; each choice
may carry a ``>`` rationale line saying *why* — the teaching payload that most
quiz formats drop on the floor.

A *bundle* is a directory of question files plus a ``manifest.json`` that declares
the exam's domains and their syllabus weights — the blueprint. Rubric can then tell
you whether a question bank actually matches the blueprint it claims to cover.

Public API::

    from rubric import QuestionDSLParser, validate_dsl, ParseResult, ParseError
    from rubric import Bundle, DomainCoverage

    result = validate_dsl(open("question.md").read())
    if result.success:
        print(result.data["question_text"])

    bundle = Bundle.load("examples/waec/mathematics/manifest.json")
    for row in bundle.coverage():
        print(row.domain, row.target_weight, row.actual_weight)
"""

from .parser import (
    QuestionDSLParser,
    ParseResult,
    ParseError,
    validate_dsl,
)
from .bundle import Bundle, DomainCoverage, BundleError

__all__ = [
    "QuestionDSLParser",
    "ParseResult",
    "ParseError",
    "validate_dsl",
    "Bundle",
    "DomainCoverage",
    "BundleError",
]

__version__ = "0.1.0"
