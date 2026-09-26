"""
Rubric command-line interface.

    rubric validate PATH        # lint a question file, a directory, or a bundle
    rubric blueprint MANIFEST   # show how a bank's coverage matches its blueprint

``validate`` exits non-zero when anything fails to parse, so it drops straight
into CI or a pre-commit hook. ``blueprint`` prints the coverage table and, with
``--strict``, exits non-zero when a domain needs attention — a blueprint domain
that is under-covered or empty, or a question tagged with a domain the blueprint
never declared — the check that keeps a bank honest against the syllabus it
advertises.

Both commands accept ``--json`` and emit the versioned report documented in
``docs/JSON-OUTPUT.md``. The human table and the JSON are two renderings of one
report object built in ``rubric.report``, so they cannot disagree. Exit codes are
the same either way.
"""

from __future__ import annotations

import argparse
import glob
import os
import sys
from typing import List

from .bundle import Bundle, BundleError
from .report import (
    build_blueprint_report,
    build_validate_report,
    dump_json,
    error_report,
    render_blueprint,
    render_validate,
)


def _fail(as_json: bool, command: str, message: str, exit_code: int = 2) -> int:
    """Report a structural failure — JSON on stdout, or a human line on stderr."""
    if as_json:
        print(dump_json(error_report(command, message, exit_code)))
    else:
        print(f"error: {message}", file=sys.stderr)
    return exit_code


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
    try:
        files = _question_files_for(args.path)
    except BundleError as exc:
        return _fail(args.json, "validate", str(exc))

    if not files:
        return _fail(args.json, "validate", f"No question files found under {args.path}")

    report = build_validate_report(args.path, files)
    print(dump_json(report) if args.json else render_validate(report, args.verbose))
    return report["exit_code"]


# ---- blueprint -------------------------------------------------------------


def cmd_blueprint(args: argparse.Namespace) -> int:
    try:
        bundle = Bundle.load(args.manifest)
    except BundleError as exc:
        return _fail(args.json, "blueprint", str(exc))

    report = build_blueprint_report(bundle, strict=args.strict)
    print(dump_json(report) if args.json else render_blueprint(report))
    return report["exit_code"]


# ---- entrypoint ------------------------------------------------------------


_JSON_HELP = "emit the versioned machine-readable report (see docs/JSON-OUTPUT.md)"


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="rubric",
        description="Lint and analyse git-native exam-prep question banks.",
    )
    sub = p.add_subparsers(dest="command", required=True)

    v = sub.add_parser("validate", help="lint a question file, directory, or bundle manifest")
    v.add_argument("path", help="a .md question, a directory, or a manifest.json")
    v.add_argument("-v", "--verbose", action="store_true", help="also print warnings")
    v.add_argument("--json", action="store_true", help=_JSON_HELP)
    v.set_defaults(func=cmd_validate)

    b = sub.add_parser("blueprint", help="report domain coverage against a bundle manifest")
    b.add_argument("manifest", help="path to a bundle manifest.json")
    b.add_argument(
        "--strict",
        action="store_true",
        help="exit non-zero if any domain needs attention (under-covered, empty, or off-blueprint)",
    )
    b.add_argument("--json", action="store_true", help=_JSON_HELP)
    b.set_defaults(func=cmd_blueprint)

    return p


def main(argv: List[str] | None = None) -> int:
    # Domain names can carry characters outside a legacy Windows console's code
    # page; degrade unprintable characters instead of aborting with UnicodeEncodeError.
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[union-attr]
    except (AttributeError, ValueError):
        pass
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
