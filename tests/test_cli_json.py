"""Golden-fixture tests for the CLI's ``--json`` reports.

The JSON shape is a published contract (`docs/JSON-OUTPUT.md`), so it is pinned
the same way the parser output is: a fixture per command under
``tests/cli_json/``, byte-compared against what the CLI prints. A change that
edits one of these files is a change to the contract and has to be deliberate.

Two things are deliberately *not* in the fixtures:

* ``rubric_version`` — it tracks the package version, so it is asserted
  separately and popped before the comparison. Bumping the release must not
  rewrite every fixture.
* absolute paths — every command is run with the working directory at the repo
  root, and report paths are repo-relative with ``/`` separators, so the fixtures
  are identical on Windows and Linux.

Regenerate after an intentional change:  ``python tests/cli_json/regen.py``
"""

import io
import json
import os
import sys

import pytest

import rubric
from rubric.cli import main
from rubric.report import SCHEMA_VERSION

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FIXTURES = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cli_json")

# Each case: fixture name, argv, expected exit code.
CASES = [
    # A directory holding one clean question, one that only warns, and one that
    # fails — so a single fixture pins all three per-file statuses.
    ("validate_dir", ["validate", "--json", "tests/cli_json/inputs"], 1),
    # A whole bundle, resolved through its manifest.
    ("validate_bundle", ["validate", "--json", "examples/interactive-demo/manifest.json"], 0),
    # A structural failure: there is no bank to report on, so the payload is the
    # error form — a non-zero exit is not the only signal.
    (
        "validate_error_missing_manifest",
        ["validate", "--json", "tests/cli_json/inputs/absent/manifest.json"],
        2,
    ),
    # Coverage with real gaps, under --strict.
    (
        "blueprint_comptia_strict",
        ["blueprint", "--strict", "--json", "examples/comptia-security-plus/manifest.json"],
        1,
    ),
    # Coverage of an evenly covered bank.
    (
        "blueprint_waec_math",
        ["blueprint", "--json", "examples/waec/mathematics/manifest.json"],
        0,
    ),
]


def run_json(argv):
    """Run the CLI from the repo root and return ``(exit_code, parsed_report)``."""
    cwd = os.getcwd()
    stdout = sys.stdout
    buf = io.StringIO()
    try:
        os.chdir(REPO_ROOT)
        sys.stdout = buf
        code = main(argv)
    finally:
        sys.stdout = stdout
        os.chdir(cwd)
    return code, json.loads(buf.getvalue())


def load_fixture(name):
    with open(os.path.join(FIXTURES, name + ".json"), "r", encoding="utf-8") as fh:
        return json.load(fh)


@pytest.mark.parametrize("name,argv,expected_exit", CASES, ids=[c[0] for c in CASES])
def test_json_report_matches_fixture(name, argv, expected_exit):
    code, report = run_json(argv)
    assert code == expected_exit
    assert report.pop("rubric_version") == rubric.__version__
    assert report == load_fixture(name)


@pytest.mark.parametrize("name,argv,expected_exit", CASES, ids=[c[0] for c in CASES])
def test_every_report_declares_the_schema_version(name, argv, expected_exit):
    """``schema_version`` is the contract's anchor — present on every payload."""
    _, report = run_json(argv)
    assert report["schema_version"] == SCHEMA_VERSION
    assert isinstance(report["schema_version"], int)


@pytest.mark.parametrize("name,argv,expected_exit", CASES, ids=[c[0] for c in CASES])
def test_exit_code_field_agrees_with_the_process_exit_code(name, argv, expected_exit):
    """A pipeline reading only the JSON must reach the same verdict as a shell."""
    code, report = run_json(argv)
    assert report["exit_code"] == code


def test_validation_failure_is_representable_in_json():
    """A failing question is *described*, not merely signalled by a non-zero exit.

    The point of the flag: a consumer can tell which file failed and why, from
    the payload alone.
    """
    code, report = run_json(["validate", "--json", "tests/cli_json/inputs"])
    assert code == 1
    assert report["ok"] is False
    assert report["summary"]["failed"] == 1

    failed = [f for f in report["files"] if f["status"] == "fail"]
    assert len(failed) == 1
    assert failed[0]["path"] == "tests/cli_json/inputs/broken.md"
    assert failed[0]["errors"], "a failed file must carry its errors"
    assert all({"line", "message", "severity"} <= set(e) for e in failed[0]["errors"])
    assert any("## Choices" in e["message"] for e in failed[0]["errors"])

    # And a warning is reported without being confused for a failure.
    warned = [f for f in report["files"] if f["status"] == "warn"]
    assert len(warned) == 1
    assert warned[0]["warnings"][0]["severity"] == "warning"


def test_structural_error_is_representable_in_json():
    code, report = run_json(
        ["blueprint", "--json", "tests/cli_json/inputs/absent/manifest.json"]
    )
    assert code == 2
    assert report["ok"] is False
    assert report["exit_code"] == 2
    assert "error" in report and report["error"]
    assert report["command"] == "blueprint"


# ---- human and JSON output cannot disagree ---------------------------------


def test_human_and_json_are_built_from_one_report():
    """The human table renders the same report object the JSON dumps.

    Asserted by rendering both from the report and checking the numbers the human
    summary claims are exactly the ones in the payload.
    """
    from rubric.bundle import Bundle
    from rubric.report import (
        build_blueprint_report,
        build_validate_report,
        render_blueprint,
        render_validate,
    )
    from rubric.cli import _question_files_for

    target = os.path.join(REPO_ROOT, "tests", "cli_json", "inputs")
    report = build_validate_report(target, _question_files_for(target))
    human = render_validate(report, verbose=True)
    s = report["summary"]
    assert f"{s['passed']}/{s['total']} passed" in human
    assert f"{s['failed']} FAILED" in human
    assert human.count("FAIL ") == s["failed"]
    assert human.count("WARN ") == s["warned"]

    manifest = os.path.join(REPO_ROOT, "examples", "comptia-security-plus", "manifest.json")
    breport = build_blueprint_report(Bundle.load(manifest), strict=True)
    bhuman = render_blueprint(breport)
    assert f"{breport['problems']} domain(s) need attention" in bhuman
    for row in breport["domains"]:
        assert row["domain"][:34] in bhuman


def test_json_flag_does_not_change_the_exit_codes():
    """Exit codes are the pre-existing CI contract; ``--json`` must not move them."""
    cwd = os.getcwd()
    try:
        os.chdir(REPO_ROOT)
        for argv in (
            ["validate", "tests/cli_json/inputs"],
            ["blueprint", "--strict", "examples/comptia-security-plus/manifest.json"],
            ["validate", "tests/cli_json/inputs/absent/manifest.json"],
        ):
            buf, stdout = io.StringIO(), sys.stdout
            sys.stdout = buf
            try:
                plain = main(argv)
                with_json = main(argv + ["--json"])
            finally:
                sys.stdout = stdout
            assert plain == with_json, argv
    finally:
        os.chdir(cwd)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
