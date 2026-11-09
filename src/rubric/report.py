"""
Machine-readable reports for the ``rubric`` CLI.

Every CLI command builds a plain ``dict`` *report* here, and then either renders
it as the human table or dumps it as JSON. There is deliberately **one** code
path: the human output is a rendering of the same report the ``--json`` flag
prints, so the two can never disagree about what was found.

The JSON shape is a contract — see ``docs/JSON-OUTPUT.md``. It carries a
``schema_version``; new fields may be added without bumping it, and anything
that removes or redefines a field bumps it.

Paths in a report are normalised: relative to the working directory when they
sit under it, always with forward slashes. That keeps output diffable across
platforms and keeps a developer's home directory out of a CI log.
"""

from __future__ import annotations

import json
import os
from typing import Any, Dict, List, Optional

from . import __version__
from .bundle import Bundle
from .parser import QuestionDSLParser

#: Bumped only by a breaking change to the report shape. Additive fields do not
#: bump it, so a consumer must ignore fields it does not know.
SCHEMA_VERSION = 1


# ---- shared helpers --------------------------------------------------------


def display_path(path: str) -> str:
    """A portable, stable rendering of a filesystem path.

    Relative to the working directory when the path is under it, otherwise left
    as-is, and always with ``/`` separators so the same bank produces the same
    report text on Windows and Linux.
    """
    try:
        rel = os.path.relpath(path, os.getcwd())
    except ValueError:  # different drive on Windows
        rel = path
    if rel.split(os.sep)[0] == os.pardir:
        rel = path
    return rel.replace(os.sep, "/")


def _issue(err: Any) -> Dict[str, Any]:
    """A ParseError → the report's issue object."""
    return {"line": err.line, "message": err.message, "severity": err.severity}


def dump_json(report: Dict[str, Any]) -> str:
    """Serialise a report: stable key order, UTF-8 kept as UTF-8."""
    return json.dumps(report, indent=2, sort_keys=True, ensure_ascii=False)


def error_report(command: str, message: str, exit_code: int = 2) -> Dict[str, Any]:
    """A report for a usage/structural failure (missing manifest, empty path).

    Distinct from a question that merely fails to validate: there is no bank to
    report on, so the payload carries only the reason and the exit code.
    """
    return {
        "schema_version": SCHEMA_VERSION,
        "rubric_version": __version__,
        "command": command,
        "ok": False,
        "error": message,
        "exit_code": exit_code,
    }


# ---- validate --------------------------------------------------------------


def build_validate_report(target: str, files: List[str]) -> Dict[str, Any]:
    """Parse every file and describe the outcome.

    ``target`` is the path the user asked about; ``files`` the resolved question
    files (a manifest expands to the files it references, a directory to its
    ``*.md``, a file to itself).
    """
    parser = QuestionDSLParser()
    rows: List[Dict[str, Any]] = []
    failed = 0
    warned = 0

    for path in files:
        row: Dict[str, Any] = {"path": display_path(path), "errors": [], "warnings": []}
        try:
            with open(path, "r", encoding="utf-8") as fh:
                result = parser.parse(fh.read())
        except OSError as exc:
            row["status"] = "unreadable"
            row["errors"] = [{"line": 0, "message": f"could not read: {exc}", "severity": "error"}]
            failed += 1
            rows.append(row)
            continue

        row["errors"] = [_issue(e) for e in result.errors]
        row["warnings"] = [_issue(w) for w in result.warnings]
        if not result.success:
            row["status"] = "fail"
            failed += 1
        elif result.warnings:
            row["status"] = "warn"
            warned += 1
        else:
            row["status"] = "pass"
        rows.append(row)

    return {
        "schema_version": SCHEMA_VERSION,
        "rubric_version": __version__,
        "command": "validate",
        "target": display_path(target),
        "ok": failed == 0,
        "summary": {
            "total": len(files),
            "passed": len(files) - failed,
            "failed": failed,
            "warned": warned,
        },
        "files": rows,
        "exit_code": 1 if failed else 0,
    }


def render_validate(report: Dict[str, Any], verbose: bool = False) -> str:
    """The human form of a validate report — identical information, read by eye."""
    lines: List[str] = []
    for row in report["files"]:
        if row["status"] in ("fail", "unreadable"):
            lines.append(f"FAIL {row['path']}")
            for err in row["errors"]:
                if row["status"] == "unreadable":
                    lines.append(f"     {err['message']}")
                else:
                    lines.append(f"     line {err['line']}: {err['message']}")
        elif row["status"] == "warn" and verbose:
            lines.append(f"WARN {row['path']}")
            for w in row["warnings"]:
                lines.append(f"     line {w['line']}: {w['message']}")

    s = report["summary"]
    summary = f"\n{s['passed']}/{s['total']} passed"
    if s["warned"]:
        summary += f", {s['warned']} with warnings"
    if s["failed"]:
        summary += f", {s['failed']} FAILED"
    lines.append(summary)
    return "\n".join(lines)


# ---- blueprint -------------------------------------------------------------


_STATUS_MARK = {
    "ok": "ok  ",
    "under": "UNDER",
    "over": "over",
    "uncovered": "NONE",
    "orphan": "ORPHAN",
}


def build_blueprint_report(bundle: Bundle, strict: bool = False) -> Dict[str, Any]:
    """Describe a bank's domain coverage against its declared blueprint."""
    cert = bundle.manifest.get("certification", {})
    if not isinstance(cert, dict):
        cert = {}
    vendor = bundle.manifest.get("vendor", {})
    if not isinstance(vendor, dict):
        vendor = {}
    title = cert.get("name") or vendor.get("name") or display_path(bundle.root)

    rows = bundle.coverage()
    failures = bundle.validate()
    for f in failures:
        f["file"] = f["file"].replace(os.sep, "/")

    domains: List[Dict[str, Any]] = []
    problems = 0
    for r in rows:
        if r.status in ("under", "uncovered", "orphan"):
            problems += 1
        domains.append(
            {
                "domain": r.domain,
                "target_weight": r.target_weight,
                "actual_weight": r.actual_weight,
                "question_count": r.question_count,
                "delta": r.delta,
                "in_blueprint": r.in_blueprint,
                "status": r.status,
            }
        )

    n_files = len(bundle.question_files)
    n_failed = len(failures)

    return {
        "schema_version": SCHEMA_VERSION,
        "rubric_version": __version__,
        "command": "blueprint",
        "manifest": display_path(bundle.manifest_path),
        "title": title,
        "format_note": bundle.format_note,
        "blueprint_domains": len(bundle.blueprint),
        "strict": bool(strict),
        "ok": problems == 0 and n_failed == 0,
        "questions": {
            "files": n_files,
            "parsed": n_files - n_failed,
            "failed": n_failed,
        },
        "domains": domains,
        "problems": problems,
        "failures": failures,
        "exit_code": 1 if (strict and problems) else 0,
    }


def render_blueprint(report: Dict[str, Any]) -> str:
    """The human coverage table — the same numbers the JSON report carries."""
    lines: List[str] = []
    if report["format_note"]:
        lines.append(f"note: {report['format_note']}\n")

    q = report["questions"]
    count_line = f"{q['parsed']} questions"
    if q["failed"]:
        count_line += f" ({q['failed']} failed to parse, excluded from the percentages)"

    n_declared = report["blueprint_domains"]
    lines.append(f"Blueprint coverage - {report['title']}")
    lines.append(f"{count_line} across {n_declared} declared domains\n")

    header = f"  {'domain':<34}{'target':>8}{'actual':>8}{'count':>7}{'delta':>8}  status"
    lines.append(header)
    lines.append("  " + "-" * (len(header) - 2))

    for d in report["domains"]:
        target = "-" if d["target_weight"] is None else f"{d['target_weight']:g}%"
        actual = f"{d['actual_weight']:g}%"
        delta = "-" if d["delta"] is None else f"{d['delta']:+g}"
        mark = _STATUS_MARK.get(d["status"], d["status"])
        lines.append(
            f"  {d['domain'][:34]:<34}{target:>8}{actual:>8}"
            f"{d['question_count']:>7}{delta:>8}  {mark}"
        )

    lines.append("")
    if report["problems"]:
        lines.append(
            f"{report['problems']} domain(s) need attention "
            "(under-covered, empty, or off-blueprint)."
        )
    else:
        lines.append("Every blueprint domain is represented within tolerance.")
    return "\n".join(lines)
