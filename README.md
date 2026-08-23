# Rubric

**An open, git-native format for exam-prep question banks — where the unit of value is the *teaching*, not the score.**

[![License: Apache 2.0](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.9%2B-blue.svg)](pyproject.toml)

A Rubric question is a plain Markdown file: YAML frontmatter for metadata, a Markdown body for the prompt and choices. It reads like something a teacher would write, diffs cleanly in a pull request, and parses into structured data with a single dependency (PyYAML).

```markdown
---
type: SINGLE_CHOICE
domains: [Number and Numeration]
difficulty: EASY
explanation: |
  Three-fifths of 200 is (3 ÷ 5) × 200 = 120.
---

# Question

A farmer harvests 200 mangoes and sells three-fifths of them. How many does she sell?

## Choices

A. 120 *[CORRECT]*
> (3 ÷ 5) × 200 = 120. "Three-fifths of 200" is the fraction times the whole.
B. 40
> This is one-fifth of 200 — you found one part but forgot to multiply by the 3.
C. 60
> You found a fifth, then divided again instead of multiplying by the 3.
D. 333
> You divided by the fraction instead of multiplying. Dividing by a number < 1 makes
> the answer *bigger* than 200 — a useful sanity check.
```

---

## Why another quiz format?

There are already good ways to write a quiz as text — GIFT, QTI, `text2qti`, R/exams, and others. Rubric is **not** trying to be a better general quiz format, and if all you need is "author questions and score them," those tools are excellent and you should use them.

Rubric exists because three things that matter most for *exam preparation* are usually treated as afterthoughts:

### 1. The rationale is a first-class citizen — per **choice**

Some formats *can* attach feedback to individual answers — GIFT and QTI among them — but it's an optional extra that's easy to skip and usually skipped. Rubric makes the per-choice rationale the default unit of a question, because a learner didn't get it wrong in the abstract — they picked **B**, for a specific reason. A distractor *is* a misconception, and the `>` rationale line addresses the mistake the learner actually made:

```markdown
B. Oxygen
> A common trap: oxygen is a *product* of photosynthesis, not an input. It's an input
> of respiration — the reverse process — which is exactly why the two get confused.
```

The rationale is the teaching payload. It's the thing a good tutor says and a scoring engine throws away.

### 2. The syllabus is executable — a **blueprint**, not a folder of files

A real exam isn't a flat pile of questions; it's a weighted distribution across domains. WAEC Mathematics is 25% each across four areas. CompTIA Security+ SY0-701 is 12 / 22 / 18 / 28 / 20 across five. Rubric captures that weighting in a bundle `manifest.json` and then **checks your question bank against it** — so "we cover the syllabus" stops being a claim and becomes a number you can see in CI.

### 3. The bank is **yours** — git-native, no lock-in

It's Markdown in a git repo. No database, no proprietary export, no lock-in. Fork it, diff it, review it in a PR, and take it with you.

---

## Install

```bash
pip install rubric-dsl
```

Or from source:

```bash
git clone https://github.com/obilabs/rubric
cd rubric
pip install -e ".[dev]"
```

## Use it as a library

```python
from rubric import validate_dsl

result = validate_dsl(open("question.md").read())
if result.success:
    q = result.data
    print(q["question_text"])
    for choice in q["choices"]:
        mark = "✓" if choice["is_correct"] else " "
        print(f"  [{mark}] {choice['letter']}. {choice['text']}")
        if choice["rationale"]:
            print(f"        → {choice['rationale']}")
else:
    for err in result.errors:
        print(f"line {err.line}: {err.message}")
```

## Use it from the command line

**Lint** a file, a directory, or a whole bundle — exits non-zero on any error, so it drops into CI or a pre-commit hook:

```console
$ rubric validate examples/waec/mathematics/manifest.json

60/60 passed, 1 with warnings
```

**Check coverage** against the blueprint. Here is the bundled CompTIA Security+ starter set — deliberately incomplete, so you can see the gaps it surfaces:

```console
$ rubric blueprint examples/comptia-security-plus/manifest.json
Blueprint coverage - CompTIA Security+ (SY0-701)
7 questions across 5 declared domains

  domain                              target  actual  count   delta  status
  -------------------------------------------------------------------------
  General Security Concepts              12%   28.6%      2   +16.6  over
  Threats, Vulnerabilities, and Miti     22%   28.6%      2    +6.6  ok
  Security Architecture                  18%      0%      0     -18  NONE
  Security Operations                    28%   42.9%      3   +14.9  over
  Security Program Management and Ov     20%      0%      0     -20  NONE

2 domain(s) need attention (under-covered, empty, or off-blueprint).
```

At a glance: a learner drilling this bank would be blindsided on Security Architecture and Security Program Management — 38% of the real exam, 0% of the questions. `--strict` turns that into a failing exit code for CI.

---

## What's in the box

| Piece | Where | What it does |
|---|---|---|
| **Parser** | `rubric.QuestionDSLParser`, `rubric.validate_dsl` | Markdown+YAML → structured `dict`, with line-located errors and warnings |
| **Bundle** | `rubric.Bundle` | Loads a manifest, validates its files, computes domain coverage vs. blueprint weights |
| **CLI** | `rubric validate`, `rubric blueprint` | Lint banks and report syllabus coverage |
| **Examples** | `examples/` | 360 WAEC questions across 7 subjects + a CompTIA Security+ starter — AI-generated seed content at enough volume to exercise the parser and the coverage tool |

### Question types

| Type | Status |
|---|---|
| `SINGLE_CHOICE` / `MULTIPLE_CHOICE` | ✅ full |
| `MULTIPLE_SELECT` | ✅ full |
| `TRUE_FALSE` | ✅ full |
| `CASE_STUDY` (scenario + nested sub-questions) | ✅ full |
| `HOTSPOT` (click-a-region, JSON coordinates) | ⚠️ parses; renderer is downstream |
| `DRAG_DROP`, `SIMULATION` | 🚧 reserved — parse to a stub today |

See [`docs/FORMAT.md`](docs/FORMAT.md) for the complete syntax reference, and [`ROADMAP.md`](ROADMAP.md) for where this is going (short version: an in-browser **playground** that renders a bank and shows a learner which *domains* to improve).

---

## The example corpus

`examples/waec/` contains 360 questions across seven WAEC subjects; `examples/comptia-security-plus/` a hand-authored Security+ starter. **These are AI-generated seed content, clearly labelled as such in each manifest — not transcriptions of real past papers.** They exist to exercise the format at scale and to give the coverage tool something real to measure. Review before using any of it for actual study.

Rubric is domain-agnostic: the same format carries a West African secondary-school maths bank and a professional IT certification bank without changing a line of the parser. Bringing your own exam is a matter of writing a `manifest.json` with your domains and their weights.

> **Trademarks.** CompTIA® and Security+® are marks of CompTIA; WAEC and WASSCE are marks of the West African Examinations Council. Rubric and ObiLabs are not affiliated with or endorsed by them — exam names and their published domain weightings are referenced descriptively from public sources.

---

## Contributing

Issues and PRs welcome. Because Rubric is Apache-2.0, contributions come in under the same license — no CLA needed. Good first contributions: a new example bundle for an exam you know, a renderer, or a JS/WASM port of the parser (see the roadmap).

## License

[Apache-2.0](LICENSE). A permissive license on purpose — Rubric is meant to be embedded, forked, and built on.

Rubric is an [ObiLabs](https://obilabs.dev) project.
