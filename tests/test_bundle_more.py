"""Extra Bundle tests: real coverage aggregation, structural guards, and the
two bugs fixed after the pre-launch review (scalar `domains`, non-numeric weight)."""

import json
import os

import pytest
from rubric import Bundle, BundleError


def _q(domains_yaml: str) -> str:
    """A minimal valid SINGLE_CHOICE question with the given `domains:` value."""
    return (
        f"---\ntype: SINGLE_CHOICE\ndomains: {domains_yaml}\n---\n"
        "# Question\nq?\n## Choices\nA. x *[CORRECT]*\nB. y\n"
    )


def _write_bundle(tmp_path, domains, questions, fmt="rubric-bundle/v1"):
    """Write a manifest + question files under tmp_path; return the manifest path.

    `questions` is a list of (filename, content) pairs.
    """
    qdir = tmp_path / "questions"
    qdir.mkdir()
    files = []
    for name, content in questions:
        (qdir / name).write_text(content, encoding="utf-8")
        files.append(f"questions/{name}")
    manifest = {"format": fmt, "domains": domains, "question_files": files}
    path = tmp_path / "manifest.json"
    path.write_text(json.dumps(manifest), encoding="utf-8")
    return str(path)


# ---- validate() failure aggregation ---------------------------------------

def test_validate_reports_broken_files(tmp_path):
    manifest = _write_bundle(
        tmp_path,
        [{"name": "D", "weight": 100}],
        [("good.md", _q("[D]")), ("broken.md", "not a question at all")],
    )
    failures = Bundle.load(manifest).validate()
    assert len(failures) == 1
    assert failures[0]["file"] == os.path.join("questions", "broken.md")
    assert failures[0]["errors"]


# ---- coverage() produces real over/under/orphan rows -----------------------

def test_coverage_over_under_orphan(tmp_path):
    manifest = _write_bundle(
        tmp_path,
        [{"name": "A", "weight": 50}, {"name": "B", "weight": 50}],
        [
            ("q1.md", _q("[A]")),
            ("q2.md", _q("[A]")),
            ("q3.md", _q("[A]")),
            ("q4.md", _q("[C]")),  # C is not in the blueprint -> orphan
        ],
    )
    rows = {r.domain: r for r in Bundle.load(manifest).coverage()}
    assert rows["A"].question_count == 3
    assert rows["A"].status == "over"          # 75% actual vs 50% target
    assert rows["B"].status == "uncovered"     # declared, zero questions
    assert rows["C"].status == "orphan"        # tagged but not declared
    assert rows["C"].target_weight is None


# ---- the fixed bugs --------------------------------------------------------

def test_scalar_domains_not_split_into_letters(tmp_path):
    """A scalar `domains:` value counts as one domain, not one per character."""
    manifest = _write_bundle(
        tmp_path,
        [{"name": "Algebra", "weight": 100}],
        [("q1.md", _q("Algebra"))],  # scalar, not a YAML list
    )
    rows = {r.domain: r for r in Bundle.load(manifest).coverage()}
    assert rows["Algebra"].question_count == 1
    # No bogus single-letter orphan domains from char-by-char iteration.
    assert "A" not in rows and "l" not in rows and "g" not in rows


def test_numeric_string_weight_is_coerced(tmp_path):
    manifest = _write_bundle(
        tmp_path,
        [{"name": "A", "weight": "50"}],  # quoted number
        [("q1.md", _q("[A]"))],
    )
    row = {r.domain: r for r in Bundle.load(manifest).coverage()}["A"]
    assert row.target_weight == 50.0


def test_non_numeric_weight_disables_target(tmp_path):
    manifest = _write_bundle(
        tmp_path,
        [{"name": "A", "weight": "high"}],  # not a number
        [("q1.md", _q("[A]"))],
    )
    row = {r.domain: r for r in Bundle.load(manifest).coverage()}["A"]
    assert row.target_weight is None
    assert row.status == "ok"  # present with questions, no target to compare


# ---- format note + structural guards ---------------------------------------

def test_unknown_format_notes_best_effort(tmp_path):
    manifest = _write_bundle(tmp_path, [], [("q1.md", _q("[A]"))], fmt="bogus/v9")
    bundle = Bundle.load(manifest)
    assert bundle.format_note is not None
    assert "unrecognised" in bundle.format_note


def test_manifest_not_object_raises(tmp_path):
    path = tmp_path / "manifest.json"
    path.write_text(json.dumps(["not", "an", "object"]), encoding="utf-8")
    with pytest.raises(BundleError):
        Bundle.load(str(path))


def test_question_files_not_list_raises(tmp_path):
    path = tmp_path / "manifest.json"
    path.write_text(
        json.dumps({"format": "rubric-bundle/v1", "domains": [], "question_files": "nope"}),
        encoding="utf-8",
    )
    with pytest.raises(BundleError):
        Bundle.load(str(path))


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
