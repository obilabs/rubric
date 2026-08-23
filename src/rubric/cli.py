"""
Rubric command-line interface.

    rubric validate PATH        # lint a question file, a directory, or a bundle
    rubric blueprint MANIFEST   # show how a bank's coverage matches its blueprint

``validate`` exits non-zero when anything fails to parse, so it drops straight
into CI or a pre-commit hook. ``blueprint`` prints the coverage table and, with
``--strict``, exits non-zero when a blueprint domain is under-covered or empty —
the check that keeps a question bank honest against the syllabus it advertises.
"""

from __future__ import annotations

import argparse
import glob
import os
import sys
from typing import List

from .parser import QuestionDSLParser
from .bundle import Bundle, BundleError


# ---- validate --------------------------------------------------------------


def _question_files_for(path: str) -> List[str]:
    """Resolve a CLI path to a list of question files to check.

    A ``manifest.json`` expands to exactly the files it references (order and
    all); a directory expands to every ``*.md`` under it; a file is itself.
    """
    if os.path.basename(path) == "manifest.json":
        return Bundle.load(path).question_files
    if os.path.isdir(path):
        return sorted(glob.glob(os.path.join(path, "**", "*.md"), recursive=True))
    return [path]


def cmd_validate(args: argparse.Namespace) -> int:
    parser = QuestionDSLParser()
    try:
        files = _question_files_for(args.path)
    except BundleError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    if not files:
        print(f"No question files found under {args.path}", file=sys.stderr)
        return 2

    failed = 0
    warned = 0
    for path in files:
        try:
            with open(path, "r", encoding="utf-8") as fh:
                result = parser.parse(fh.read())
        except OSError as exc:
            print(f"FAIL {path}\n     could not read: {exc}")
            failed += 1
            continue

        if not result.success:
            failed += 1
            print(f"FAIL {path}")
            for err in result.errors:
                print(f"     line {err.line}: {err.message}")
        elif result.warnings:
            warned += 1
            if args.verbose:
                print(f"WARN {path}")
                for w in result.warnings:
                    print(f"     line {w.line}: {w.message}")

    ok = len(files) - failed
    summary = f"\n{ok}/{len(files)} passed"
    if warned:
        summary += f", {warned} with warnings"
    if failed:
        summary += f", {failed} FAILED"
    print(summary)
    return 1 if failed else 0


# ---- blueprint -------------------------------------------------------------


_STATUS_MARK = {
    "ok": "ok  ",
    "under": "UNDER",
    "over": "over",
    "uncovered": "NONE",
    "orphan": "ORPHAN",
}


def cmd_blueprint(args: argparse.Namespace) -> int:
    try:
        bundle = Bundle.load(args.manifest)
    except BundleError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    if bundle.format_note:
        print(f"note: {bundle.format_note}\n")

    cert = bundle.manifest.get("certification", {})
    title = cert.get("name") or bundle.manifest.get("vendor", {}).get("name") or bundle.root
    rows = bundle.coverage()
    total = sum(r.question_count for r in rows if r.in_blueprint)

    print(f"Blueprint coverage - {title}")
    print(f"{len(bundle.question_files)} questions across {len(bundle.blueprint)} declared domains\n")

    header = f"  {'domain':<34}{'target':>8}{'actual':>8}{'count':>7}{'delta':>8}  status"
    print(header)
    print("  " + "-" * (len(header) - 2))

    problems = 0
    for r in rows:
        target = "-" if r.target_weight is None else f"{r.target_weight:g}%"
        actual = f"{r.actual_weight:g}%"
        delta = "-" if r.delta is None else f"{r.delta:+g}"
        mark = _STATUS_MARK.get(r.status, r.status)
        if r.status in ("under", "uncovered", "orphan"):
            problems += 1
        print(f"  {r.domain[:34]:<34}{target:>8}{actual:>8}{r.question_count:>7}{delta:>8}  {mark}")

    print()
    if problems:
        print(f"{problems} domain(s) need attention (under-covered, empty, or off-blueprint).")
    else:
        print("Every blueprint domain is represented within tolerance.")

    if args.strict and problems:
        return 1
    return 0


# ---- entrypoint ------------------------------------------------------------


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="rubric",
        description="Lint and analyse git-native exam-prep question banks.",
    )
    sub = p.add_subparsers(dest="command", required=True)

    v = sub.add_parser("validate", help="lint a question file, directory, or bundle manifest")
    v.add_argument("path", help="a .md question, a directory, or a manifest.json")
    v.add_argument("-v", "--verbose", action="store_true", help="also print warnings")
    v.set_defaults(func=cmd_validate)

    b = sub.add_parser("blueprint", help="report domain coverage against a bundle manifest")
    b.add_argument("manifest", help="path to a bundle manifest.json")
    b.add_argument(
        "--strict",
        action="store_true",
        help="exit non-zero if any blueprint domain is under-covered or empty",
    )
    b.set_defaults(func=cmd_blueprint)

    return p


def main(argv: List[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
