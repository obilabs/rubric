"""Tests for the Bundle loader and blueprint-coverage check."""

import json
import os

import pytest
from rubric import Bundle, DomainCoverage, BundleError

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MATH_MANIFEST = os.path.join(REPO_ROOT, "examples", "waec", "mathematics", "manifest.json")


class TestBundleLoad:
    def test_loads_real_math_bundle(self):
        bundle = Bundle.load(MATH_MANIFEST)
        # 4 domains x 15 questions = 60 files declared in the manifest.
        assert len(bundle.question_files) == 60
        assert len(bundle.blueprint) == 4
        # Native corpus manifests carry the native format id — no legacy note.
        assert bundle.format_note is None

    def test_missing_manifest_raises(self):
        with pytest.raises(BundleError):
            Bundle.load(os.path.join(REPO_ROOT, "examples", "waec", "nope", "manifest.json"))

    def test_missing_question_file_raises(self, tmp_path):
        manifest = tmp_path / "manifest.json"
        manifest.write_text(
            json.dumps(
                {
                    "format": "rubric-bundle/v1",
                    "domains": [{"name": "X", "weight": 100}],
                    "question_files": ["questions/does-not-exist.md"],
                }
            ),
            encoding="utf-8",
        )
        with pytest.raises(BundleError):
            Bundle.load(str(manifest))

    def test_legacy_format_is_accepted_with_a_note(self, tmp_path):
        manifest = tmp_path / "manifest.json"
        manifest.write_text(
            json.dumps(
                {
                    "format": "examgenie-content-bundle/v1",
                    "domains": [],
                    "question_files": [],
                }
            ),
            encoding="utf-8",
        )
        bundle = Bundle.load(str(manifest))
        assert bundle.format_note is not None
        assert "legacy" in bundle.format_note


class TestCoverage:
    def test_math_bundle_validates_clean(self):
        bundle = Bundle.load(MATH_MANIFEST)
        assert bundle.validate() == []

    def test_coverage_matches_blueprint(self):
        bundle = Bundle.load(MATH_MANIFEST)
        rows = {r.domain: r for r in bundle.coverage()}
        # The four WAEC maths domains are each weighted 25 and each hold 15 of 60.
        for name in [
            "Number and Numeration",
            "Algebraic Processes",
            "Geometry and Mensuration",
            "Statistics and Probability",
        ]:
            row = rows[name]
            assert isinstance(row, DomainCoverage)
            assert row.in_blueprint is True
            assert row.question_count == 15
            assert row.target_weight == 25
            assert row.actual_weight == 25
            assert row.status == "ok"

    def test_uncovered_domain_is_flagged(self):
        """A blueprint domain with no questions reports 'uncovered'."""
        cov = DomainCoverage(
            domain="Untouched", target_weight=25, question_count=0,
            actual_weight=0.0, in_blueprint=True,
        )
        assert cov.status == "uncovered"

    def test_under_covered_domain_is_flagged(self):
        cov = DomainCoverage(
            domain="Thin", target_weight=25, question_count=1,
            actual_weight=5.0, in_blueprint=True,
        )
        assert cov.status == "under"
        assert cov.delta == -20.0

    def test_orphan_domain_is_flagged(self):
        cov = DomainCoverage(
            domain="Off-syllabus", target_weight=None, question_count=3,
            actual_weight=10.0, in_blueprint=False,
        )
        assert cov.status == "orphan"
        assert cov.delta is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
