"""
Bundle — a manifest-declared set of Rubric questions, and the coverage check
that makes the exam blueprint executable.

A bundle directory looks like::

    mathematics/
      manifest.json
      questions/
        algebraic-processes-001.md
        number-and-numeration-001.md
        ...

The manifest declares the exam's *domains* and their syllabus *weights* — the
blueprint. ``Bundle.coverage()`` parses every question, tallies how many land in
each domain, and reports the actual distribution against the declared weights.
That turns "our question bank covers the syllabus" from a claim into a number:
you can see, in CI, that Geometry is weighted 25% of the exam but only 8% of your
bank — the gap a learner would feel as under-preparation.

Only the standard library plus PyYAML (via the parser) is used.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .parser import QuestionDSLParser, ParseResult


class BundleError(Exception):
    """Raised when a manifest cannot be read or is structurally invalid."""


# Manifest format identifiers this loader understands. The first is native to
# Rubric; the second is accepted for backward compatibility with banks authored
# before the format was extracted, and surfaces a note rather than an error.
NATIVE_FORMAT = "rubric-bundle/v1"
LEGACY_FORMATS = {"examgenie-content-bundle/v1"}


def _coerce_weight(weight) -> Optional[float]:
    """Best-effort numeric domain weight.

    Accepts an int/float, or a numeric string like ``"25"`` (a manifest hand-
    edited so the weight is quoted). Returns None for anything non-numeric, so a
    mistyped weight disables the over/under check for that domain rather than
    crashing — booleans are treated as non-numeric on purpose (``true`` is not 1%).
    """
    if isinstance(weight, bool):
        return None
    if isinstance(weight, (int, float)):
        return float(weight)
    if isinstance(weight, str):
        try:
            return float(weight.strip())
        except ValueError:
            return None
    return None


@dataclass
class DomainCoverage:
    """How one domain's actual question share compares to its blueprint weight."""

    domain: str
    target_weight: Optional[float]  # declared % of the exam, or None if not in blueprint
    question_count: int
    actual_weight: float            # this domain's % of the parsed bank
    in_blueprint: bool

    @property
    def delta(self) -> Optional[float]:
        """actual − target, in percentage points (None if no target declared)."""
        if self.target_weight is None:
            return None
        return round(self.actual_weight - self.target_weight, 1)

    @property
    def status(self) -> str:
        """A coarse label for the gap: ok | under | over | uncovered | orphan."""
        if not self.in_blueprint:
            return "orphan"          # questions tagged with a domain the blueprint never declared
        if self.question_count == 0:
            return "uncovered"       # blueprint domain with no questions at all
        d = self.delta
        if d is None:
            return "ok"
        if d <= -10:
            return "under"
        if d >= 10:
            return "over"
        return "ok"


@dataclass
class Bundle:
    """A loaded manifest plus the resolved paths of its question files."""

    manifest_path: str
    manifest: Dict[str, Any]
    root: str                       # directory the manifest lives in
    question_files: List[str] = field(default_factory=list)  # absolute paths
    format_note: Optional[str] = None  # set when a non-native manifest format was accepted

    # ---- loading -----------------------------------------------------------

    @classmethod
    def load(cls, manifest_path: str) -> "Bundle":
        """Read a manifest.json and resolve its referenced question files.

        Raises BundleError on a missing/unparseable manifest or missing files —
        those are structural faults in the bank, distinct from a question that
        merely fails DSL validation (which ``coverage``/``validate`` report).
        """
        if not os.path.isfile(manifest_path):
            raise BundleError(f"Manifest not found: {manifest_path}")
        try:
            with open(manifest_path, "r", encoding="utf-8") as fh:
                manifest = json.load(fh)
        except (json.JSONDecodeError, OSError) as exc:
            raise BundleError(f"Could not read manifest {manifest_path}: {exc}") from exc
        if not isinstance(manifest, dict):
            raise BundleError("Manifest must be a JSON object")

        root = os.path.dirname(os.path.abspath(manifest_path))

        fmt = manifest.get("format")
        format_note = None
        if fmt in LEGACY_FORMATS:
            format_note = f"accepted legacy manifest format '{fmt}' (native is '{NATIVE_FORMAT}')"
        elif fmt != NATIVE_FORMAT:
            format_note = f"unrecognised manifest format '{fmt}' — proceeding on a best-effort basis"

        rel_files = manifest.get("question_files", [])
        if not isinstance(rel_files, list):
            raise BundleError("Manifest 'question_files' must be a list")

        resolved: List[str] = []
        missing: List[str] = []
        for rel in rel_files:
            path = os.path.join(root, rel)
            (resolved if os.path.isfile(path) else missing).append(path)
        if missing:
            raise BundleError(
                f"{len(missing)} question file(s) referenced by the manifest are missing, "
                f"e.g. {os.path.relpath(missing[0], root)}"
            )

        return cls(
            manifest_path=os.path.abspath(manifest_path),
            manifest=manifest,
            root=root,
            question_files=resolved,
            format_note=format_note,
        )

    # ---- accessors ---------------------------------------------------------

    @property
    def blueprint(self) -> List[Dict[str, Any]]:
        """The declared domains, each ``{name, weight, ...}``."""
        domains = self.manifest.get("domains", [])
        return domains if isinstance(domains, list) else []

    def parse_all(self) -> List[ParseResult]:
        """Parse every question file, in manifest order."""
        parser = QuestionDSLParser()
        results = []
        for path in self.question_files:
            with open(path, "r", encoding="utf-8") as fh:
                results.append(parser.parse(fh.read()))
        return results

    def validate(self) -> List[Dict[str, Any]]:
        """Return one row per question that failed to parse.

        Each row is ``{file, errors}`` with repo-relative paths, so a caller
        (CLI, CI) can fail loudly and point at the offending file.
        """
        parser = QuestionDSLParser()
        failures = []
        for path in self.question_files:
            with open(path, "r", encoding="utf-8") as fh:
                result = parser.parse(fh.read())
            if not result.success:
                failures.append(
                    {
                        "file": os.path.relpath(path, self.root),
                        "errors": [e.message for e in result.errors],
                    }
                )
        return failures

    # ---- the differentiator: blueprint coverage ----------------------------

    def coverage(self) -> List[DomainCoverage]:
        """Compare the bank's actual per-domain distribution to the blueprint.

        A question contributes to every domain listed in its frontmatter
        ``domains``. Domains are matched to the blueprint by name. Blueprint
        domains with no questions surface as ``uncovered``; question domains not
        in the blueprint surface as ``orphan``. Rows come back blueprint-first
        (in declared order), then any orphans.
        """
        # Tally questions per domain name.
        counts: Dict[str, int] = {}
        total = 0
        for result in self.parse_all():
            if not result.success or not result.data:
                continue
            total += 1
            domains = result.data.get("domains") or []
            # A scalar `domains:` in frontmatter (e.g. `domains: Algebra`) parses
            # to a string; iterating it directly would tally it character by
            # character. Wrap non-list values so one domain counts once.
            if isinstance(domains, str):
                domains = [domains]
            elif not isinstance(domains, list):
                domains = []
            for name in domains:
                counts[name] = counts.get(name, 0) + 1

        def pct(n: int) -> float:
            return round(100.0 * n / total, 1) if total else 0.0

        rows: List[DomainCoverage] = []
        seen = set()
        for entry in self.blueprint:
            name = entry.get("name")
            if not name:
                continue
            seen.add(name)
            weight = entry.get("weight")
            rows.append(
                DomainCoverage(
                    domain=name,
                    target_weight=_coerce_weight(weight),
                    question_count=counts.get(name, 0),
                    actual_weight=pct(counts.get(name, 0)),
                    in_blueprint=True,
                )
            )
        # Orphans: tagged in questions but never declared in the blueprint.
        for name, n in counts.items():
            if name not in seen:
                rows.append(
                    DomainCoverage(
                        domain=name,
                        target_weight=None,
                        question_count=n,
                        actual_weight=pct(n),
                        in_blueprint=False,
                    )
                )
        return rows
