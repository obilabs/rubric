"""Conformance corpus — the Python half of the two-parser parity guard.

Rubric ships a reference parser (``src/rubric``) and a JavaScript port
(``web/rubric.js``). ``tests/conformance/build.py`` freezes a shared corpus of
inputs and the golden output the reference parser produces for each. This test
asserts the reference parser STILL reproduces those goldens, so:

  * the golden files can never drift out of sync with the Python parser
    unnoticed (change the parser's behaviour and this goes red), and
  * the goldens the JS parity test compares against are always current.

If this test fails after an intended parser change, regenerate the corpus with
``python tests/conformance/build.py`` and review the diff.
"""

from __future__ import annotations

import json
import os

import pytest

from rubric import validate_dsl, Bundle

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, ".."))
CASES_DIR = os.path.join(HERE, "conformance", "cases")
EXPECTED_DIR = os.path.join(HERE, "conformance", "expected")
COV_DIR = os.path.join(HERE, "conformance", "expected_coverage")
EXAMPLES = os.path.join(REPO, "examples")


def _case_names():
    if not os.path.isdir(EXPECTED_DIR):
        return []
    return sorted(
        f[:-5] for f in os.listdir(EXPECTED_DIR) if f.endswith(".json")
    )


def _serialize(result):
    def diag(d):
        return {"line": d.line, "message": d.message, "severity": d.severity}

    return {
        "success": result.success,
        "data": result.data,
        "errors": [diag(e) for e in result.errors],
        "warnings": [diag(w) for w in result.warnings],
    }


CASE_NAMES = _case_names()


def test_corpus_is_present():
    assert CASE_NAMES, (
        "no conformance goldens found — run `python tests/conformance/build.py`"
    )


@pytest.mark.parametrize("name", CASE_NAMES)
def test_reference_parser_matches_golden(name):
    with open(os.path.join(CASES_DIR, name + ".md"), "r", encoding="utf-8") as fh:
        dsl = fh.read()
    with open(os.path.join(EXPECTED_DIR, name + ".json"), "r", encoding="utf-8") as fh:
        expected = json.load(fh)

    actual = _serialize(validate_dsl(dsl))
    assert actual == expected, (
        f"reference parser output for '{name}' no longer matches its golden; "
        f"if this change is intended, regenerate with "
        f"`python tests/conformance/build.py`"
    )


def test_every_case_has_a_golden_and_vice_versa():
    cases = {f[:-3] for f in os.listdir(CASES_DIR) if f.endswith(".md")}
    goldens = set(CASE_NAMES)
    assert cases == goldens, (
        f"case/golden mismatch — only in cases: {cases - goldens}; "
        f"only in expected: {goldens - cases}"
    )


# ---- coverage goldens (the engine behind the playground's diagnosis) --------


def _find_manifests(root):
    out = []
    for dirpath, _dirs, files in os.walk(root):
        if "manifest.json" in files:
            out.append(os.path.join(dirpath, "manifest.json"))
    return sorted(out)


def _bundle_id(bundle):
    cert = bundle.manifest.get("certification", {})
    return (
        cert.get("slug")
        or bundle.manifest.get("slug")
        or os.path.relpath(bundle.root, EXAMPLES).replace(os.sep, "-")
    )


def _serialize_coverage(rows):
    return [
        {
            "domain": r.domain,
            "target_weight": r.target_weight,
            "question_count": r.question_count,
            "actual_weight": r.actual_weight,
            "in_blueprint": r.in_blueprint,
            "delta": r.delta,
            "status": r.status,
        }
        for r in rows
    ]


COVERAGE_MANIFESTS = _find_manifests(EXAMPLES) if os.path.isdir(EXAMPLES) else []


@pytest.mark.parametrize(
    "manifest_path", COVERAGE_MANIFESTS, ids=lambda p: os.path.basename(os.path.dirname(p))
)
def test_reference_coverage_matches_golden(manifest_path):
    bundle = Bundle.load(manifest_path)
    golden_path = os.path.join(COV_DIR, _bundle_id(bundle) + ".json")
    assert os.path.isfile(golden_path), (
        f"no coverage golden for {manifest_path}; regenerate with "
        f"`python tests/conformance/build.py`"
    )
    with open(golden_path, "r", encoding="utf-8") as fh:
        expected = json.load(fh)
    actual = _serialize_coverage(bundle.coverage())
    assert actual == expected, (
        f"coverage for '{_bundle_id(bundle)}' no longer matches its golden; "
        f"if intended, regenerate with `python tests/conformance/build.py`"
    )
