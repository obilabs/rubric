#!/usr/bin/env python3
"""Cross-model accuracy check for a Rubric bank.

Questions written by one model (e.g. the Gemini generator) are verified by a
DIFFERENT model so they don't share blind spots. The check is BLIND: each
question is stripped of its answer key and handed to the verifier cold; the
verifier solves it independently and its answer is compared to the real key. A
mismatch means either a wrong key or an ambiguous question — both are things you
want to catch.

Method (matches the generate → verify → backfill pipeline):

  1. Blind every question (remove the *[CORRECT]* marker / the pairs / the order).
  2. A PANEL of N fast verifiers (default Fable) answers each question blind.
  3. If the panel unanimously agrees with the key -> confirmed.
     Otherwise a stronger JUDGE (default Sonnet) answers it blind; the question
     is confirmed only if the judge also agrees, else it is rejected.
  4. --apply deletes rejected questions; re-run the generator with --resume to
     backfill to target, then re-run this check.

Zero third-party deps: HTTP is stdlib urllib, the DSL parser is the `rubric`
package. Needs `rubric` importable and ANTHROPIC_API_KEY set:

    ANTHROPIC_API_KEY=... python scripts/verify.py path/to/bank [--apply]

Models default to claude-fable-5 (panel) and claude-sonnet-5 (judge); override
with --panel-model / --judge-model. The blinding and comparison are pure and
have a self-test: `python scripts/verify.py --self-test`.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed

try:
    from rubric import Bundle, validate_dsl
except ImportError:  # pragma: no cover
    sys.exit("error: the 'rubric' package must be importable (use the project venv).")

ANTHROPIC_URL = "https://api.anthropic.com/v1/messages"
DEFAULT_PANEL_MODEL = "claude-fable-5"
DEFAULT_JUDGE_MODEL = "claude-sonnet-5"
DEFAULT_PANEL_SIZE = 3


# --------------------------------------------------------------------------- #
# Blinding — strip the answer key, keep only what a solver needs
# --------------------------------------------------------------------------- #

def blind_single_choice(data):
    lines = [data["question_text"], "", "Options:"]
    key = None
    for c in data["choices"]:
        lines.append(f'{c["letter"]}. {c["text"]}')
        if c.get("is_correct"):
            key = c["letter"]
    ask = ('Work out the single correct option yourself. Respond with ONLY a JSON '
           'object: {"letter": "<the correct option letter>"}')
    return "\n".join(lines), ask, {"letter": key}


def blind_drag_drop(data):
    qd = data["question_data"]
    lines = [data["question_text"], "", "Items:"]
    lines += [f'- {d["text"]}' for d in qd["draggables"]]
    lines += ["", "Targets:"]
    lines += [f'- {z["text"]}' for z in qd["dropzones"]]
    ask = ('Match each item to the single correct target, using the exact target '
           'text. Respond with ONLY a JSON object: '
           '{"pairs": [{"item": "<item>", "target": "<target>"}, ...]}')
    key = {"pairs": [{"item": p["draggable"], "target": p["dropzone"]}
                     for p in qd["pairs"]]}
    return "\n".join(lines), ask, key


def blind_simulation(data):
    qd = data["question_data"]
    pool = sorted([s["text"] for s in qd["steps"]]
                  + [d["text"] for d in qd.get("distractors", [])])
    lines = ["Task: " + data["question_text"], "", "Available actions:"]
    lines += [f"- {a}" for a in pool]
    ask = ('Some actions are distractors that do NOT belong. Select ONLY the '
           'correct actions and put them in the right order, using the exact '
           'action text. Respond with ONLY a JSON object: '
           '{"order": ["<first action>", "<second action>", ...]}')
    key = {"order": [s["text"] for s in qd["steps"]]}
    return "\n".join(lines), ask, key


BLINDERS = {
    "SINGLE_CHOICE": blind_single_choice,
    "MULTIPLE_CHOICE": blind_single_choice,
    "DRAG_DROP": blind_drag_drop,
    "SIMULATION": blind_simulation,
}


# --------------------------------------------------------------------------- #
# Comparison — did the verifier's blind answer match the key?
# --------------------------------------------------------------------------- #

def _norm(s: str) -> str:
    return re.sub(r"\s+", " ", str(s or "").strip().lower()).rstrip(".")


def compare(answer: dict, key: dict, qtype: str):
    """Return (agrees: bool, proposed: str) — proposed is the verifier's answer."""
    if not isinstance(answer, dict):
        return False, str(answer)
    if qtype in ("SINGLE_CHOICE", "MULTIPLE_CHOICE"):
        got = _norm(answer.get("letter", ""))
        return got == _norm(key["letter"]), got.upper()
    if qtype == "DRAG_DROP":
        got = {_norm(p.get("item")): _norm(p.get("target"))
               for p in answer.get("pairs", []) if isinstance(p, dict)}
        want = {_norm(p["item"]): _norm(p["target"]) for p in key["pairs"]}
        proposed = "; ".join(f'{p.get("item")}→{p.get("target")}'
                             for p in answer.get("pairs", []))
        return got == want, proposed
    if qtype == "SIMULATION":
        got = [_norm(x) for x in answer.get("order", [])]
        want = [_norm(x) for x in key["order"]]
        return got == want, " → ".join(str(x) for x in answer.get("order", []))
    return False, ""


# --------------------------------------------------------------------------- #
# Anthropic Messages API (stdlib urllib)
# --------------------------------------------------------------------------- #

def anthropic_answer(question: str, ask: str, model: str, api_key: str) -> dict:
    prompt = (
        "You are an expert exam-item reviewer. Solve the following practice "
        "question independently and accurately.\n\n"
        f"{question}\n\n{ask}\n\nReturn only the JSON, no other text."
    )
    payload = json.dumps({
        "model": model,
        "max_tokens": 1024,
        "messages": [{"role": "user", "content": prompt}],
    }).encode("utf-8")

    for attempt in range(5):
        req = urllib.request.Request(
            ANTHROPIC_URL, data=payload, method="POST",
            headers={"x-api-key": api_key, "anthropic-version": "2023-06-01",
                     "content-type": "application/json"},
        )
        try:
            with urllib.request.urlopen(req, timeout=120) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            break
        except urllib.error.HTTPError as e:
            if e.code in (429, 529, 503):
                time.sleep(5 * (attempt + 1))
                continue
            raise RuntimeError(f"Anthropic HTTP {e.code}: "
                               f"{e.read().decode('utf-8', 'replace')[:300]}") from e
        except (urllib.error.URLError, TimeoutError):
            time.sleep(5)
            continue
    else:
        raise RuntimeError("Anthropic call failed after retries")

    text = "".join(b.get("text", "") for b in data.get("content", []))
    return _extract_json(text)


def _extract_json(text: str) -> dict:
    m = re.search(r"\{.*\}", text, re.DOTALL)
    if not m:
        return {}
    try:
        return json.loads(m.group(0))
    except json.JSONDecodeError:
        return {}


# --------------------------------------------------------------------------- #
# Orchestration
# --------------------------------------------------------------------------- #

def load_items(bank_dir):
    bundle = Bundle.load(os.path.join(bank_dir, "manifest.json"))
    items = []
    for path in bundle.question_files:
        data = validate_dsl(open(path, encoding="utf-8").read()).data
        if not data or data["type"] not in BLINDERS:
            continue
        question, ask, key = BLINDERS[data["type"]](data)
        items.append({"id": os.path.splitext(os.path.basename(path))[0],
                      "file": path, "type": data["type"],
                      "question": question, "ask": ask, "key": key})
    return items


def verify_bank(bank_dir, panel_size, panel_model, judge_model, api_key,
                apply=False, workers=8):
    items = load_items(bank_dir)
    print(f"Verifying {len(items)} questions — panel {panel_size}×{panel_model}, "
          f"judge {judge_model}\n")

    def panel_vote(item):
        agree = 0
        proposals = []
        for _ in range(panel_size):
            ans = anthropic_answer(item["question"], item["ask"], panel_model, api_key)
            ok, proposed = compare(ans, item["key"], item["type"])
            agree += 1 if ok else 0
            proposals.append(proposed)
        return item, agree, proposals

    results = []
    with ThreadPoolExecutor(max_workers=workers) as ex:
        futs = [ex.submit(panel_vote, it) for it in items]
        for fut in as_completed(futs):
            item, agree, proposals = fut.result()
            if agree == panel_size:
                verdict = "confirmed"
                by = f"panel {agree}/{panel_size}"
            else:
                jans = anthropic_answer(item["question"], item["ask"], judge_model, api_key)
                jok, jprop = compare(jans, item["key"], item["type"])
                verdict = "confirmed" if jok else "rejected"
                by = f"panel {agree}/{panel_size}, judge {'agrees' if jok else 'disagrees'} ({jprop})"
            results.append({"id": item["id"], "type": item["type"],
                            "verdict": verdict, "by": by, "file": item["file"],
                            "panel_agree": agree})
            mark = "OK " if verdict == "confirmed" else "DROP"
            print(f"  [{mark}] {item['id']:<45} {by}")

    rejected = [r for r in results if r["verdict"] == "rejected"]
    print(f"\n{len(results) - len(rejected)}/{len(results)} confirmed, "
          f"{len(rejected)} rejected.")
    if rejected:
        print("Rejected:")
        for r in rejected:
            print(f"  - {r['id']} ({r['by']})")
    if apply and rejected:
        for r in rejected:
            os.remove(r["file"])
        _prune_manifest(bank_dir)
        print(f"\nDeleted {len(rejected)} rejected question file(s) and pruned the "
              f"manifest. Re-run the generator with --resume to backfill to target.")
    return results


def _prune_manifest(bank_dir):
    """Drop question_files entries whose file no longer exists, so the bank stays
    loadable after --apply even without a backfill run."""
    mpath = os.path.join(bank_dir, "manifest.json")
    with open(mpath, encoding="utf-8") as fh:
        m = json.load(fh)
    m["question_files"] = [q for q in m.get("question_files", [])
                           if os.path.isfile(os.path.join(bank_dir, q))]
    with open(mpath, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(m, fh, ensure_ascii=False, indent=2)
        fh.write("\n")


# --------------------------------------------------------------------------- #
# Self-test (pure logic — no API needed)
# --------------------------------------------------------------------------- #

def self_test():
    sc = validate_dsl(
        "---\ntype: SINGLE_CHOICE\ndomains: [D]\n---\n# Question\nq\n"
        "## Choices\nA. wrong\nB. right *[CORRECT]*\nC. wrong\n").data
    q, ask, key = blind_single_choice(sc)
    assert "*[CORRECT]*" not in q and key == {"letter": "B"}
    assert compare({"letter": "B"}, key, "SINGLE_CHOICE")[0] is True
    assert compare({"letter": "a"}, key, "SINGLE_CHOICE")[0] is False

    dd = validate_dsl(
        "---\ntype: DRAG_DROP\ndomains: [D]\n---\n# Question\nq\n"
        "## Draggables\n- A\n- B\n## Dropzones\n- 1\n- 2\n"
        "## Pairs\n- A -> 1\n- B -> 2\n").data
    _q, _ask, key = blind_drag_drop(dd)
    assert compare({"pairs": [{"item": "A", "target": "1"},
                              {"item": "B", "target": "2"}]}, key, "DRAG_DROP")[0]
    assert not compare({"pairs": [{"item": "A", "target": "2"},
                                  {"item": "B", "target": "1"}]}, key, "DRAG_DROP")[0]

    sim = validate_dsl(
        "---\ntype: SIMULATION\ndomains: [D]\n---\n# Task\nt\n"
        "## Steps\n1. first\n2. second\n## Distractors\n- trap\n").data
    q, _ask, key = blind_simulation(sim)
    assert "trap" in q and key == {"order": ["first", "second"]}
    assert compare({"order": ["first", "second"]}, key, "SIMULATION")[0]
    assert not compare({"order": ["second", "first"]}, key, "SIMULATION")[0]
    assert not compare({"order": ["first", "second", "trap"]}, key, "SIMULATION")[0]
    print("self-test: OK")


def main(argv=None):
    ap = argparse.ArgumentParser(description="Cross-model accuracy check for a Rubric bank.")
    ap.add_argument("bank", nargs="?", help="bank dir (contains manifest.json)")
    ap.add_argument("--panel-size", type=int, default=DEFAULT_PANEL_SIZE)
    ap.add_argument("--panel-model", default=DEFAULT_PANEL_MODEL)
    ap.add_argument("--judge-model", default=DEFAULT_JUDGE_MODEL)
    ap.add_argument("--apply", action="store_true", help="delete rejected questions")
    ap.add_argument("--emit-blind", metavar="DIR",
                    help="write blinded questions to DIR and exit (no API calls)")
    ap.add_argument("--self-test", action="store_true", help="run pure-logic self-test")
    args = ap.parse_args(argv)

    if args.self_test:
        self_test()
        return 0
    if not args.bank:
        ap.error("bank dir is required (or use --self-test)")

    if args.emit_blind:
        items = load_items(args.bank)
        os.makedirs(args.emit_blind, exist_ok=True)
        for it in items:
            with open(os.path.join(args.emit_blind, it["id"] + ".txt"),
                      "w", encoding="utf-8", newline="\n") as fh:
                fh.write(it["question"] + "\n\n" + it["ask"] + "\n")
        with open(os.path.join(args.emit_blind, "_keys.json"),
                  "w", encoding="utf-8", newline="\n") as fh:
            json.dump([{"id": it["id"], "type": it["type"], "key": it["key"]}
                       for it in items], fh, ensure_ascii=False, indent=2)
        print(f"wrote {len(items)} blinded questions + _keys.json to {args.emit_blind}")
        return 0

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        sys.exit("error: ANTHROPIC_API_KEY is not set")
    verify_bank(args.bank, args.panel_size, args.panel_model, args.judge_model,
                api_key, apply=args.apply)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
