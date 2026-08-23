"""Tests for the `rubric` CLI: exit-code contract and path resolution.

The exit codes are a CI contract (0 = clean, 1 = failures/strict-gaps, 2 = usage
error), so they are asserted directly here — none of this was covered before.
"""

import os

import pytest
from rubric.cli import main, _question_files_for

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MATH_MANIFEST = os.path.join(REPO_ROOT, "examples", "waec", "mathematics", "manifest.json")
COMPTIA_MANIFEST = os.path.join(REPO_ROOT, "examples", "comptia-security-plus", "manifest.json")
RATIONALE_DIR = os.path.join(REPO_ROOT, "examples", "rationale")
RATIONALE_FILE = os.path.join(RATIONALE_DIR, "fractions-of-a-quantity.md")


# ---- validate exit codes ---------------------------------------------------

def test_validate_clean_file_exit_0():
    assert main(["validate", RATIONALE_FILE]) == 0


def test_validate_clean_bundle_exit_0():
    assert main(["validate", MATH_MANIFEST]) == 0


def test_validate_broken_file_exit_1(tmp_path):
    f = tmp_path / "broken.md"
    f.write_text("no frontmatter here", encoding="utf-8")
    assert main(["validate", str(f)]) == 1


def test_validate_missing_manifest_exit_2(tmp_path):
    missing = tmp_path / "manifest.json"  # does not exist
    assert main(["validate", str(missing)]) == 2


def test_validate_empty_dir_exit_2(tmp_path):
    assert main(["validate", str(tmp_path)]) == 2


# ---- blueprint exit codes --------------------------------------------------

def test_blueprint_balanced_bundle_exit_0():
    # The WAEC maths bundle is evenly covered; no --strict, so always 0.
    assert main(["blueprint", MATH_MANIFEST]) == 0


def test_blueprint_without_strict_is_0_even_with_gaps():
    # CompTIA starter has empty domains, but plain blueprint only reports.
    assert main(["blueprint", COMPTIA_MANIFEST]) == 0


def test_blueprint_strict_flags_gaps_exit_1():
    # Two empty domains -> --strict must fail.
    assert main(["blueprint", "--strict", COMPTIA_MANIFEST]) == 1


def test_blueprint_strict_clean_bundle_exit_0():
    assert main(["blueprint", "--strict", MATH_MANIFEST]) == 0


def test_blueprint_missing_manifest_exit_2(tmp_path):
    assert main(["blueprint", str(tmp_path / "manifest.json")]) == 2


# ---- _question_files_for branches ------------------------------------------

def test_resolve_manifest_expands_to_referenced_files():
    files = _question_files_for(MATH_MANIFEST)
    assert len(files) == 60


def test_resolve_directory_globs_markdown():
    files = _question_files_for(RATIONALE_DIR)
    assert len(files) == 2
    assert all(f.endswith(".md") for f in files)


def test_resolve_single_file_returns_itself():
    files = _question_files_for(RATIONALE_FILE)
    assert files == [RATIONALE_FILE]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
