#!/usr/bin/env python3
"""Generate a Rubric question-bank bundle with Google Gemini.

Rubric's whole point is the *teaching payload*: every choice carries a `>`
rationale naming the misconception it represents. This generator bakes that in.
It produces the three interactive types Rubric cares about — SINGLE_CHOICE (with
per-choice rationale), DRAG_DROP, and SIMULATION — and validates every single
question through the real parser (`from rubric import validate_dsl`) before it is
written. Anything the model emits that does not parse, or that is missing its
rationale, is discarded and regenerated.

Zero third-party deps: HTTP is stdlib `urllib.request`, the DSL validator is the
`rubric` package itself. Run under an interpreter that has `rubric` importable
(e.g. the project venv):

    # single (type, domain) run
    python scripts/generate.py \
        --vendor-name Microsoft --vendor-slug microsoft \
        --cert-name "Azure Fundamentals (AZ-900)" --code AZ-900 \
        --slug azure-az-900 --passing-score 700 \
        --domain "Cloud Concepts" --weight 25 \
        --hint "IaaS/PaaS/SaaS, public/private/hybrid, CapEx vs OpEx, high availability" \
        --type SINGLE_CHOICE --count 5

    # whole multi-domain bundle from a JSON spec (cleanest)
    python scripts/generate.py --spec my-cert.json

A spec file looks like::

    {
      "vendor":      {"name": "Microsoft", "slug": "microsoft",
                      "description": "..."},
      "certification": {"name": "Azure Fundamentals (AZ-900)", "code": "AZ-900",
                        "slug": "azure-az-900", "description": "...",
                        "passing_score": 700, "difficulty_level": "beginner",
                        "exam_duration_minutes": 60},
      "default_type": "SINGLE_CHOICE",
      "domains": [
        {"name": "Cloud Concepts", "weight": 25, "hint": "...", "count": 4},
        {"name": "Azure Architecture and Services", "weight": 35, "hint": "...",
         "count": 4, "type": "DRAG_DROP"},
        {"name": "Management and Governance", "weight": 30, "hint": "...",
         "count": 3, "type": "SIMULATION"}
      ]
    }

Output bundle layout::

    <out>/<slug>/manifest.json
    <out>/<slug>/questions/<domain-slug>-NNN.md   # one question per file, LF

The manifest is `format: "rubric-bundle/v1"` and is rebuilt from whatever files
exist on disk, so a run interrupted by an API quota still leaves a valid bundle.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
import unicodedata
import urllib.error
import urllib.request
from pathlib import Path

try:
    from rubric import validate_dsl
except ImportError:  # pragma: no cover - guidance only
    sys.exit(
        "error: the 'rubric' package is not importable. Run this under an "
        "interpreter that has it installed, e.g. the project venv:\n"
        "    D:/tmp/rubric-venv/Scripts/python.exe scripts/generate.py ..."
    )

DEFAULT_MODEL = "gemini-2.5-flash"
GEMINI_URL_TMPL = (
    "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
)
SEP = "====="  # multi-question separator the prompts ask the model to emit
QUESTION_TYPES = ("SINGLE_CHOICE", "DRAG_DROP", "SIMULATION")


# --------------------------------------------------------------------------- #
# Gemini call (stdlib urllib, with 429/backoff handling à la exam_genie)
# --------------------------------------------------------------------------- #

class QuotaExhausted(Exception):
    """Raised when the API keeps returning 429 — the daily quota is gone."""


_consecutive_429 = 0


def gemini_generate(prompt: str, api_key: str, model: str,
                    temperature: float = 0.8) -> str:
    """POST one prompt to Gemini and return the concatenated text parts.

    Retries transient network errors and 429s (backing off harder each time);
    raises QuotaExhausted after 5 consecutive 429s so the caller can stop and
    leave a valid partial bundle behind.
    """
    global _consecutive_429
    url = GEMINI_URL_TMPL.format(model=model)
    payload = json.dumps({
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": temperature, "maxOutputTokens": 16384},
    }).encode("utf-8")

    for _ in range(6):
        req = urllib.request.Request(
            url, data=payload, method="POST",
            headers={"x-goog-api-key": api_key, "Content-Type": "application/json"},
        )
        try:
            with urllib.request.urlopen(req, timeout=180) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            _consecutive_429 = 0
            break
        except urllib.error.HTTPError as e:
            if e.code == 429:
                _consecutive_429 += 1
                if _consecutive_429 >= 5:
                    raise QuotaExhausted(
                        "5 consecutive 429s — daily quota exhausted; resume with "
                        "--resume once it resets"
                    )
                time.sleep(30 * _consecutive_429)
                continue
            body = e.read().decode("utf-8", "replace")[:500]
            raise RuntimeError(f"Gemini HTTP {e.code}: {body}") from e
        except (urllib.error.URLError, TimeoutError) as e:
            print(f"    network error ({e}); retrying in 10s", flush=True)
            time.sleep(10)
            continue
    else:
        raise RuntimeError("Gemini call failed after retries")

    candidates = data.get("candidates") or []
    if not candidates:
        # safety block or empty response — treat as "produced nothing this round"
        return ""
    parts = candidates[0].get("content", {}).get("parts", []) or []
    return "".join(p.get("text", "") for p in parts)


# --------------------------------------------------------------------------- #
# Prompt templates — one per type. Kept close to the real example files so the
# model emits byte-perfect DSL for the strict parser.
# --------------------------------------------------------------------------- #

_COMMON_HEAD = (
    "You are an expert {vendor} certification item-writer creating practice "
    "questions for {cert}.\n\n"
    "Write {n} high-quality {qtype} practice questions for this exam domain:\n"
    "DOMAIN: {domain}\n"
    "DOMAIN SCOPE: {hint}\n\n"
    "Output rules — follow them EXACTLY; an automated validator rejects anything "
    "that does not parse:\n"
    "1. Output ONLY question blocks. No preamble, no commentary, no numbering, no "
    "markdown code fences.\n"
    "2. Separate consecutive questions with a line containing exactly five equals "
    "signs and nothing else:\n"
    "=====\n"
    "3. Use each domain name verbatim. Keep the frontmatter line exactly:\n"
    '   domains: ["{domain}"]\n'
    "4. Do NOT put any horizontal rule ('---', '***', '___') inside a question "
    "body; the only '---' lines are the two YAML frontmatter delimiters.\n"
    "5. difficulty is one of EASY, MEDIUM, HARD — vary it across the set.\n"
    "6. Be factually accurate. Do not invent product names, CVEs, port numbers, "
    "or versions you are unsure of.\n\n"
)

PROMPT_SINGLE_CHOICE = _COMMON_HEAD + (
    "Each question is one block in this EXACT format:\n\n"
    "---\n"
    "type: SINGLE_CHOICE\n"
    'domains: ["{domain}"]\n'
    "difficulty: MEDIUM\n"
    "explanation: |\n"
    "  A 2-3 sentence explanation of the correct answer and the idea being tested.\n"
    "---\n\n"
    "# Question\n\n"
    "<a single, self-contained question or short scenario>\n\n"
    "## Choices\n\n"
    "A. <option text> *[CORRECT]*\n"
    "> <one sentence: why this option is correct>\n"
    "B. <option text>\n"
    "> <one sentence: the SPECIFIC misconception a student who picks this holds>\n"
    "C. <option text>\n"
    "> <one sentence: the specific misconception this distractor represents>\n"
    "D. <option text>\n"
    "> <one sentence: the specific misconception this distractor represents>\n\n"
    "STRICT REQUIREMENTS:\n"
    "- Between 3 and 5 options, labelled A, B, C, ... each on its own line as "
    "'<LETTER>. <text>'.\n"
    "- EXACTLY ONE option carries the marker *[CORRECT]* appended after its text, "
    "exactly as shown. Never mark two.\n"
    "- EVERY option is IMMEDIATELY followed by exactly one '>' rationale line "
    "naming the specific misconception that distractor represents (or, for the "
    "correct option, why it is right). This per-choice rationale is the entire "
    "point of the format — never omit it for any option.\n"
    "- Spread the correct answer across the letters over the whole set; do not put "
    "it on 'A' every time.\n"
)

PROMPT_DRAG_DROP = _COMMON_HEAD + (
    "Each question is one block in this EXACT format:\n\n"
    "---\n"
    "type: DRAG_DROP\n"
    'domains: ["{domain}"]\n'
    "difficulty: MEDIUM\n"
    "explanation: |\n"
    "  A 2-3 sentence explanation of the correct matching.\n"
    "---\n\n"
    "# Question\n\n"
    "<tell the student to match each draggable to the correct dropzone>\n\n"
    "## Draggables\n\n"
    "- <token A>\n"
    "- <token B>\n"
    "- <token C>\n\n"
    "## Dropzones\n\n"
    "- <target 1>\n"
    "- <target 2>\n"
    "- <target 3>\n\n"
    "## Pairs\n\n"
    "- <token A> -> <target 1>\n"
    "> <why this mapping is correct, or the common mis-pairing it guards against>\n"
    "- <token B> -> <target 2>\n"
    "> <rationale>\n"
    "- <token C> -> <target 3>\n"
    "> <rationale>\n\n"
    "STRICT REQUIREMENTS:\n"
    "- The three sections '## Draggables', '## Dropzones', '## Pairs' are all "
    "required and non-empty. Use 3-5 items each.\n"
    "- Every Pairs line is 'LEFT -> RIGHT' using the ASCII arrow '->' (hyphen "
    "greater-than).\n"
    "- LEFT must be copied CHARACTER-FOR-CHARACTER from a Draggables item and "
    "RIGHT copied CHARACTER-FOR-CHARACTER from a Dropzones item — exact string "
    "match, no trailing punctuation, no rewording, no added words.\n"
    "- Keep every draggable label and every dropzone label unique.\n"
    "- Every Pairs line is IMMEDIATELY followed by one '>' rationale line.\n"
)

PROMPT_SIMULATION = _COMMON_HEAD + (
    "Each question is one block in this EXACT format:\n\n"
    "---\n"
    "type: SIMULATION\n"
    'domains: ["{domain}"]\n'
    "difficulty: MEDIUM\n"
    "explanation: |\n"
    "  A 2-3 sentence explanation of the correct procedure.\n"
    "---\n\n"
    "# Task\n\n"
    "<a task the student must accomplish; tell them to put the actions in order>\n\n"
    "## Steps\n\n"
    "1. <first correct action>\n"
    "> <why this step, or why it must come first>\n"
    "2. <second correct action>\n"
    "> <why this step>\n"
    "3. <third correct action>\n"
    "> <why this step>\n\n"
    "## Distractors\n\n"
    "- <a wrong action offered alongside the real steps>\n"
    "> <why it is a trap>\n\n"
    "STRICT REQUIREMENTS:\n"
    "- The prompt heading is '# Task' (NOT '# Question').\n"
    "- '## Steps' is an ordered list ('1.', '2.', '3.', ...) and the order IS the "
    "correct sequence. Use 3-6 steps.\n"
    "- Every Step is IMMEDIATELY followed by one '>' rationale line.\n"
    "- Include a '## Distractors' section with 1-3 wrong actions, each as '- "
    "<action>' IMMEDIATELY followed by one '>' rationale line.\n"
)

PROMPTS = {
    "SINGLE_CHOICE": PROMPT_SINGLE_CHOICE,
    "DRAG_DROP": PROMPT_DRAG_DROP,
    "SIMULATION": PROMPT_SIMULATION,
}


# --------------------------------------------------------------------------- #
# Parsing the model output into candidate DSL blocks
# --------------------------------------------------------------------------- #

_HR_LINE = re.compile(r"^\s*(-{3,}|\*{3,}|_{3,})\s*$")


def _strip_fences(lines):
    while lines and lines[0].strip().startswith("```"):
        lines.pop(0)
    while lines and lines[-1].strip().startswith("```"):
        lines.pop()
    return lines


def sanitize_chunk(raw: str) -> str:
    """Clean one candidate block: LF newlines, drop code fences, and strip any
    stray horizontal rule from the *body* so it cannot masquerade as a
    frontmatter delimiter and truncate a section."""
    raw = raw.replace("\r\n", "\n").replace("\r", "\n").strip()
    lines = _strip_fences(raw.split("\n"))

    # locate the two frontmatter delimiters (first two lines that are exactly ---)
    delim_idx = [i for i, ln in enumerate(lines) if ln.strip() == "---"]
    if len(delim_idx) < 2:
        return "\n".join(lines).strip()
    fm_end = delim_idx[1]
    head = lines[: fm_end + 1]
    body = [ln for ln in lines[fm_end + 1:] if not _HR_LINE.match(ln)]
    return "\n".join(head + body).strip()


def split_questions(raw: str):
    for chunk in raw.split(SEP):
        chunk = sanitize_chunk(chunk)
        if chunk.startswith("---"):
            yield chunk


def force_domain(chunk: str, name: str) -> str:
    """Rewrite (or insert) the frontmatter `domains:` line to exactly the
    canonical, quoted domain name — guarantees blueprint matching and makes
    comma-containing domain names safe regardless of what the model wrote."""
    line = f'domains: ["{name}"]'
    if re.search(r"^domains:.*$", chunk, flags=re.M):
        return re.sub(r"^domains:.*$", line, chunk, count=1, flags=re.M)
    return re.sub(r"^(type:.*)$", r"\1\n" + line, chunk, count=1, flags=re.M)


def normalise(text: str) -> str:
    return re.sub(r"\W+", "", unicodedata.normalize("NFKC", text or "").lower())


# --------------------------------------------------------------------------- #
# Per-type quality checks (run on the parsed data, on top of validate_dsl)
# --------------------------------------------------------------------------- #

def _all_have_rationale(items) -> bool:
    return all((it.get("rationale") or "").strip() for it in items)


def check_question(qtype: str, data: dict):
    """Return (ok, reason). Enforces this generator's quality bar on top of a
    successful parse: the rationale that makes Rubric worth using."""
    if data.get("type") != qtype:
        return False, f"type is {data.get('type')}, expected {qtype}"
    if not (data.get("explanation") or "").strip():
        return False, "missing explanation"

    if qtype == "SINGLE_CHOICE":
        choices = data.get("choices", [])
        if not (3 <= len(choices) <= 5):
            return False, f"{len(choices)} choices (need 3-5)"
        if sum(1 for c in choices if c.get("is_correct")) != 1:
            return False, "must have exactly 1 *[CORRECT]*"
        if not _all_have_rationale(choices):
            return False, "a choice is missing its '>' rationale"
        return True, "ok"

    if qtype == "DRAG_DROP":
        qd = data.get("question_data", {})
        drag, zones, pairs = qd.get("draggables", []), qd.get("dropzones", []), qd.get("pairs", [])
        if not drag or not zones or not pairs:
            return False, "empty draggables/dropzones/pairs"
        if not _all_have_rationale(pairs):
            return False, "a pair is missing its '>' rationale"
        return True, "ok"

    if qtype == "SIMULATION":
        qd = data.get("question_data", {})
        steps, distractors = qd.get("steps", []), qd.get("distractors", [])
        if len(steps) < 2:
            return False, f"{len(steps)} steps (need >= 2)"
        if not _all_have_rationale(steps):
            return False, "a step is missing its '>' rationale"
        if not distractors:
            return False, "no distractors (need >= 1)"
        if not _all_have_rationale(distractors):
            return False, "a distractor is missing its '>' rationale"
        return True, "ok"

    return False, f"unsupported type {qtype}"


# --------------------------------------------------------------------------- #
# Bundle generation
# --------------------------------------------------------------------------- #

def domain_slug(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")


def write_text_lf(path: Path, text: str) -> None:
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text)


def generate_domain(dom: dict, qdir: Path, seen: set, api_key: str, model: str,
                    temperature: float, batch_size: int, max_rounds: int,
                    resume: bool) -> dict:
    name = dom["name"]
    qtype = dom["type"]
    target = int(dom["count"])
    hint = dom.get("hint", name)
    dslug = domain_slug(name)

    kept = len(list(qdir.glob(f"{dslug}-*.md"))) if resume else 0
    rejected = 0
    if kept >= target:
        return {"type": qtype, "target": target, "kept": kept, "rejected": 0,
                "resumed": True}

    prompt_tmpl = PROMPTS[qtype]
    rounds = 0
    while kept < target and rounds < max_rounds:
        rounds += 1
        want = min(batch_size, target - kept)
        prompt = prompt_tmpl.format(
            vendor=dom.get("vendor", ""), cert=dom.get("cert", ""),
            n=want, qtype=qtype, domain=name, hint=hint,
        )
        try:
            raw = gemini_generate(prompt, api_key, model, temperature)
        except QuotaExhausted:
            raise
        except Exception as e:  # noqa: BLE001 — log and retry next round
            print(f"  [{name}] API error: {e}; retrying in 10s", flush=True)
            time.sleep(10)
            continue

        for chunk in split_questions(raw):
            if kept >= target:
                break
            chunk = force_domain(chunk, name)
            result = validate_dsl(chunk)
            if not result.success:
                rejected += 1
                continue
            ok, _reason = check_question(qtype, result.data)
            if not ok:
                rejected += 1
                continue
            key = normalise(result.data.get("question_text", ""))
            if not key or key in seen:
                rejected += 1
                continue
            seen.add(key)
            kept += 1
            fname = f"{dslug}-{kept:03d}.md"
            write_text_lf(qdir / fname, chunk.strip() + "\n")

        print(f"  [{name}/{qtype}] kept {kept}/{target} (rejected {rejected}, "
              f"round {rounds})", flush=True)

    return {"type": qtype, "target": target, "kept": kept, "rejected": rejected}


def write_manifest(bundle_dir: Path, qdir: Path, spec: dict, model: str,
                   report: dict) -> int:
    """Rebuild manifest.json from the question files on disk, in domain order.

    Directory-driven (not an in-memory list) so an interrupted run still yields a
    valid, loadable bundle.
    """
    ordered_files = []
    for dom in spec["domains"]:
        dslug = domain_slug(dom["name"])
        for p in sorted(qdir.glob(f"{dslug}-*.md")):
            rel = f"questions/{p.name}"
            if rel not in ordered_files:
                ordered_files.append(rel)
    # include any stragglers not matching a declared domain (kept deterministic)
    for p in sorted(qdir.glob("*.md")):
        rel = f"questions/{p.name}"
        if rel not in ordered_files:
            ordered_files.append(rel)

    cert = spec["certification"]
    manifest = {
        "format": "rubric-bundle/v1",
        "vendor": spec["vendor"],
        "certification": {
            "name": cert["name"],
            "code": cert.get("code", ""),
            "slug": cert.get("slug", domain_slug(cert["name"])),
            "description": cert.get("description", ""),
            **({"difficulty_level": cert["difficulty_level"]}
               if cert.get("difficulty_level") else {}),
            **({"exam_duration_minutes": cert["exam_duration_minutes"]}
               if cert.get("exam_duration_minutes") else {}),
            "passing_score": cert.get("passing_score", 70),
        },
        "domains": [
            {"name": d["name"], "weight": d.get("weight", 0), "order": i + 1,
             "description": d.get("hint", "")}
            for i, d in enumerate(spec["domains"])
        ],
        "question_defaults": {"source": "ai_generated"},
        "question_files": ordered_files,
        "generator": {
            "model": model,
            "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "report": report,
            "note": "AI-generated content — NOT real past exam questions. These "
                    "were written by an LLM to the published exam blueprint and "
                    "should be reviewed by a subject-matter expert before use.",
        },
    }
    write_text_lf(bundle_dir / "manifest.json",
                  json.dumps(manifest, indent=2, ensure_ascii=False) + "\n")
    return len(ordered_files)


def generate_bundle(spec: dict, out_root: Path, api_key: str, model: str,
                    temperature: float, batch_size: int, max_rounds: int,
                    resume: bool, force: bool) -> None:
    slug = spec["certification"].get("slug") or domain_slug(spec["certification"]["name"])
    bundle_dir = out_root / slug
    qdir = bundle_dir / "questions"

    if qdir.exists() and any(qdir.glob("*.md")) and not resume and not force:
        sys.exit(
            f"error: {qdir} already has question files. Re-run with --resume to "
            f"top up missing questions, or --force to overwrite from scratch."
        )
    qdir.mkdir(parents=True, exist_ok=True)

    seen = set()
    if resume:
        for f in qdir.glob("*.md"):
            data = validate_dsl(f.read_text(encoding="utf-8")).data or {}
            seen.add(normalise(data.get("question_text", "")))

    report = {}
    try:
        for dom in spec["domains"]:
            dom = dict(dom)  # don't mutate caller's spec
            dom["type"] = dom.get("type", spec.get("default_type", "SINGLE_CHOICE"))
            dom["count"] = dom.get("count", spec.get("default_count", 5))
            dom["vendor"] = spec["vendor"].get("name", "")
            dom["cert"] = spec["certification"]["name"]
            if dom["type"] not in QUESTION_TYPES:
                sys.exit(f"error: domain '{dom['name']}' has unsupported type "
                         f"'{dom['type']}'. Use one of {', '.join(QUESTION_TYPES)}.")
            print(f"=== {dom['name']} ({dom['type']}, target {dom['count']}) ===",
                  flush=True)
            report[dom["name"]] = generate_domain(
                dom, qdir, seen, api_key, model, temperature,
                batch_size, max_rounds, resume,
            )
    finally:
        n = write_manifest(bundle_dir, qdir, spec, model, report)
        print(f"\n[{slug}] bundle written: {n} questions -> {bundle_dir}", flush=True)


# --------------------------------------------------------------------------- #
# Spec assembly (from --spec file or single-run CLI flags) + entrypoint
# --------------------------------------------------------------------------- #

def spec_from_args(args) -> dict:
    if not (args.vendor_name and args.cert_name and args.domain):
        sys.exit("error: for a single run supply at least --vendor-name, "
                 "--cert-name and --domain (or use --spec FILE).")
    return {
        "vendor": {
            "name": args.vendor_name,
            "slug": args.vendor_slug or domain_slug(args.vendor_name),
            "description": args.vendor_description or "",
        },
        "certification": {
            "name": args.cert_name,
            "code": args.code or "",
            "slug": args.slug or domain_slug(args.cert_name),
            "description": args.cert_description or "",
            "difficulty_level": args.difficulty_level or "",
            "exam_duration_minutes": args.duration,
            "passing_score": args.passing_score,
        },
        "default_type": args.type,
        "default_count": args.count,
        "domains": [{
            "name": args.domain,
            "weight": args.weight,
            "hint": args.hint or args.domain,
            "type": args.type,
            "count": args.count,
        }],
    }


def main(argv=None) -> int:
    repo_root = Path(__file__).resolve().parent.parent
    ap = argparse.ArgumentParser(
        description="Generate a Rubric question-bank bundle with Gemini.")
    ap.add_argument("--spec", help="path to a JSON bundle spec (multi-domain)")
    ap.add_argument("--out", default=str(repo_root / "examples"),
                    help="output root dir (default: <repo>/examples)")

    # single-run flags
    ap.add_argument("--vendor-name")
    ap.add_argument("--vendor-slug")
    ap.add_argument("--vendor-description")
    ap.add_argument("--cert-name")
    ap.add_argument("--code")
    ap.add_argument("--slug")
    ap.add_argument("--cert-description")
    ap.add_argument("--difficulty-level")
    ap.add_argument("--duration", type=int, default=None,
                    help="exam duration in minutes")
    ap.add_argument("--passing-score", type=int, default=70)
    ap.add_argument("--domain", help="single domain name")
    ap.add_argument("--weight", type=int, default=100)
    ap.add_argument("--hint", help="syllabus scope hint for the prompt")
    ap.add_argument("--type", choices=QUESTION_TYPES, default="SINGLE_CHOICE")
    ap.add_argument("--count", type=int, default=5)

    # generation controls
    ap.add_argument("--model", default=DEFAULT_MODEL)
    ap.add_argument("--temperature", type=float, default=0.8)
    ap.add_argument("--batch-size", type=int, default=5,
                    help="questions requested per API call")
    ap.add_argument("--max-rounds", type=int, default=6,
                    help="max API rounds per domain (safety valve)")
    ap.add_argument("--resume", action="store_true",
                    help="keep existing question files and top up to target")
    ap.add_argument("--force", action="store_true",
                    help="overwrite an existing bundle from scratch")
    args = ap.parse_args(argv)

    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        sys.exit("error: GEMINI_API_KEY is not set")

    if args.spec:
        spec = json.loads(Path(args.spec).read_text(encoding="utf-8"))
    else:
        spec = spec_from_args(args)

    try:
        generate_bundle(spec, Path(args.out), api_key, args.model,
                        args.temperature, args.batch_size, args.max_rounds,
                        args.resume, args.force)
    except QuotaExhausted as e:
        print(f"STOPPING: {e}", flush=True)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
