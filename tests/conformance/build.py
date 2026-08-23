#!/usr/bin/env python3
"""Generate the parser conformance corpus.

Rubric has two parsers: the reference Python one in ``src/rubric/parser.py`` and
a JavaScript port in ``web/rubric.js`` that powers the zero-backend playground.
Two implementations of one grammar can drift apart silently — the exact failure
mode this project is built to prevent. This script pins them together.

It writes, for a fixed corpus of DSL inputs:

  * ``cases/<name>.md``       — the shared input, read by BOTH test suites
  * ``expected/<name>.json``  — the golden output, produced by the REFERENCE
                                (Python) parser

``tests/test_conformance.py`` asserts the Python parser still reproduces every
golden file (so the goldens can't rot), and ``web/test/parity.test.cjs`` asserts
the JavaScript port reproduces them too. If either parser changes behaviour, its
test goes red; regenerate with this script only after an intended change.

Run from anywhere::

    python tests/conformance/build.py
"""

from __future__ import annotations

import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, os.path.join(REPO, "src"))

from rubric import validate_dsl  # noqa: E402
from rubric import Bundle  # noqa: E402


# The corpus. Each entry is (name, dsl_text). Inputs are chosen to exercise the
# grammar's branches AND the fiddly bits where a re-implementation is most
# likely to diverge: block scalars, quoted flow-sequence commas, scalar-vs-list
# domains, per-choice rationale, and every error/warning message Rubric emits
# from its OWN code (not from an underlying YAML/JSON library, whose exception
# text differs across languages and is therefore excluded from cross-parity).
CASES: list[tuple[str, str]] = [
    (
        "single_choice",
        """---
type: SINGLE_CHOICE
domains: [Security Fundamentals]
difficulty: EASY
explanation: Encryption converts plaintext to ciphertext using an algorithm and key.
---

# Question

What is the primary purpose of encryption?

## Choices

A. To make data unreadable to unauthorized users *[CORRECT]*
B. To compress data
C. To delete data
D. To backup data
""",
    ),
    (
        "single_choice_rationale",
        """---
type: SINGLE_CHOICE
domains: [Number and Numeration]
difficulty: EASY
tags: [fractions, word-problem]
explanation: |
  Three-fifths of 200 is (3 / 5) * 200 = 120. "Of" means multiply by the
  fraction; the whole (200) is what you take the fraction of.
---

# Question

A farmer harvests 200 mangoes and sells three-fifths of them at the market.
How many mangoes does she sell?

## Choices

A. 120 *[CORRECT]*
> (3 / 5) * 200 = 120. "Three-fifths of 200" is the fraction times the whole.
B. 40
> This is one-fifth of 200. You found the size of one part but forgot to
> multiply by the 3 parts the numerator asks for.
C. 60
> You divided 200 by 5 and then stopped.
D. 333
> You divided by three-fifths instead of multiplying by it.
""",
    ),
    (
        "multiple_choice_image",
        """---
type: MULTIPLE_CHOICE
domains: [Security Operations, Network Security]
difficulty: MEDIUM
tags: [firewall, networking]
explanation: |
  The firewall default deny rule blocks all traffic unless explicitly allowed.
  This is a security best practice.
---

# Question

A security analyst notices that users cannot access the internet after a firewall update.
Which of the following is the MOST likely cause?

[IMAGE: firewall-config]

## Choices

A. The firewall is blocking HTTPS traffic
B. The DNS server is misconfigured
C. The default deny rule was applied *[CORRECT]*
D. The routing table is incorrect
""",
    ),
    (
        "multiple_select",
        """---
type: MULTIPLE_SELECT
domains: [Security Fundamentals]
difficulty: EASY
---

# Question

Which of the following are components of the CIA triad? *(Select TWO)*

## Choices

A. Confidentiality *[CORRECT]*
B. Compliance
C. Integrity *[CORRECT]*
D. Authorization
E. Availability
""",
    ),
    (
        "true_false",
        """---
type: TRUE_FALSE
domains: [Security Fundamentals]
difficulty: EASY
tags: [encryption, https]
explanation: |
  HTTPS encrypts data in transit using TLS/SSL protocols.
---

# Question

HTTPS provides encryption for data transmitted between a web browser and server.

## Choices

T. TRUE *[CORRECT]*
F. FALSE
""",
    ),
    (
        "case_study",
        """---
type: CASE_STUDY
domains: [Security Operations, Incident Response]
difficulty: HARD
tags: [data-breach, incident-response]
---

# Scenario

Your organization experienced a data breach when an S3 bucket containing customer PII was
publicly exposed for 48 hours.

[IMAGE: incident-timeline]

## Question 1

What should be the FIRST priority in responding to this incident?

### Choices

A. Notify affected customers immediately
B. Isolate the affected S3 bucket *[CORRECT]*
C. Update the incident response plan
D. Conduct a full security audit

### Explanation

Isolation prevents further data exposure and should be the immediate first step.

## Question 2

Which TWO actions should be included in the remediation plan?

### Choices

A. Review and strengthen IAM policies *[CORRECT]*
B. Delete the AWS account
C. Implement comprehensive logging *[CORRECT]*
D. Disable all S3 services
E. Increase storage capacity

### Explanation

Strengthening IAM policies and implementing logging address the root causes.
""",
    ),
    (
        "hotspot",
        """---
type: HOTSPOT
domains: [Network Security]
difficulty: HARD
---

# Question

Click on the firewall interface that is configured for the DMZ network.

[IMAGE: network-diagram]

## Hotspots

```json
{
  "image": "network-diagram.png",
  "correctRegions": [
    {"x": 250, "y": 180, "width": 100, "height": 50, "label": "DMZ Interface"}
  ],
  "distractorRegions": [
    {"x": 250, "y": 80, "width": 100, "height": 50, "label": "WAN Interface"}
  ]
}
```
""",
    ),
    (
        "drag_drop_stub",
        """---
type: DRAG_DROP
domains: [Security Architecture]
difficulty: MEDIUM
---

# Question

Match each control to its category.
""",
    ),
    (
        "simulation_stub",
        """---
type: SIMULATION
domains: [Security Operations]
difficulty: HARD
---

# Question

Configure the firewall to allow only HTTPS.
""",
    ),
    (
        "domains_quoted_comma",
        """---
type: SINGLE_CHOICE
domains: ["Threats, Vulnerabilities, and Mitigations"]
difficulty: MEDIUM
---

# Question

A single domain name that contains commas must be quoted.

## Choices

A. Correct *[CORRECT]*
B. Wrong
""",
    ),
    (
        "domains_scalar",
        """---
type: SINGLE_CHOICE
domains: Algebraic Processes
difficulty: EASY
---

# Question

A scalar domains value parses to a string, not a list.

## Choices

A. Correct *[CORRECT]*
B. Wrong
""",
    ),
    (
        "explanation_strip_chomp",
        """---
type: SINGLE_CHOICE
domains: [Test]
explanation: |-
  This block scalar uses strip chomping.
  It has no trailing newline.
---

# Question

Strip-chomped block scalar.

## Choices

A. Correct *[CORRECT]*
B. Wrong
""",
    ),
    (
        "warn_bad_difficulty",
        """---
type: MULTIPLE_CHOICE
difficulty: SUPER_HARD
---

# Question

Question text

## Choices
A. Answer *[CORRECT]*
""",
    ),
    (
        "warn_rationale_before_choice",
        """---
type: SINGLE_CHOICE
domains: [Test]
---

# Question

A rationale line before any choice is a warning.

## Choices

> orphaned rationale line
A. Correct *[CORRECT]*
B. Wrong
""",
    ),
    (
        "err_no_frontmatter",
        """
# Question
This has no frontmatter

## Choices
A. Option A
""",
    ),
    (
        "err_no_type",
        """---
difficulty: MEDIUM
---

# Question
Missing type field
""",
    ),
    (
        "err_bad_type",
        """---
type: ESSAY
---

# Question
An unknown type is a hard error.
""",
    ),
    (
        "err_wrong_answer_count",
        """---
type: MULTIPLE_CHOICE
---

# Question
Multiple choice with 2 correct answers

## Choices
A. Answer A *[CORRECT]*
B. Answer B *[CORRECT]*
C. Answer C
""",
    ),
    (
        "err_missing_choices",
        """---
type: SINGLE_CHOICE
domains: [Test]
---

# Question

This question has no Choices section.
""",
    ),
    (
        "err_true_false_three_choices",
        """---
type: TRUE_FALSE
domains: [Test]
---

# Question

True/false must have exactly two choices.

## Choices

A. One *[CORRECT]*
B. Two
C. Three
""",
    ),
    (
        "err_multiple_select_too_few",
        """---
type: MULTIPLE_SELECT
domains: [Test]
---

# Question

Multiple select needs at least two correct answers.

## Choices

A. Only correct *[CORRECT]*
B. Wrong
C. Wrong
""",
    ),
    (
        "err_case_study_no_subquestions",
        """---
type: CASE_STUDY
domains: [Test]
---

# Scenario

This is a scenario with no sub-questions.
""",
    ),
]


def serialize(result) -> dict:
    """Canonical, language-neutral view of a ParseResult for golden comparison."""

    def diag(d):
        return {"line": d.line, "message": d.message, "severity": d.severity}

    return {
        "success": result.success,
        "data": result.data,
        "errors": [diag(e) for e in result.errors],
        "warnings": [diag(w) for w in result.warnings],
    }


def serialize_coverage(rows) -> list:
    """Language-neutral view of Bundle.coverage() for golden comparison.

    Mirrors exactly the fields the JS `Rubric.coverage()` returns, so the
    playground's domain diagnosis provably scores the same way `rubric
    blueprint` does in CI.
    """
    return [
        {
            "domain": r.domain,
            "target_weight": r.target_weight,
            "question_count": r.question_count,
            "actual_weight": r.actual_weight,
            "in_blueprint": r.in_blueprint,
            "delta": r.delta,
            "status": r.status,
        }
        for r in rows
    ]


def _find_manifests(root: str):
    out = []
    for dirpath, _dirs, files in os.walk(root):
        if "manifest.json" in files:
            out.append(os.path.join(dirpath, "manifest.json"))
    return sorted(out)


def main() -> int:
    cases_dir = os.path.join(HERE, "cases")
    expected_dir = os.path.join(HERE, "expected")
    cov_dir = os.path.join(HERE, "expected_coverage")
    os.makedirs(cases_dir, exist_ok=True)
    os.makedirs(expected_dir, exist_ok=True)
    os.makedirs(cov_dir, exist_ok=True)

    names = [name for name, _ in CASES]
    if len(names) != len(set(names)):
        raise SystemExit("duplicate case name in corpus")

    for name, dsl in CASES:
        # Always write LF; the repo normalizes to LF and both parsers must read
        # identical bytes for the comparison to mean anything.
        with open(
            os.path.join(cases_dir, name + ".md"), "w", encoding="utf-8", newline="\n"
        ) as fh:
            fh.write(dsl)

        result = validate_dsl(dsl)
        payload = serialize(result)
        with open(
            os.path.join(expected_dir, name + ".json"),
            "w",
            encoding="utf-8",
            newline="\n",
        ) as fh:
            json.dump(payload, fh, ensure_ascii=False, indent=2, sort_keys=True)
            fh.write("\n")

    # Coverage goldens over every real example bank — this pins the JS coverage
    # port (the engine behind the playground's "what to drill" diagnosis) to the
    # reference Bundle.coverage the CLI uses.
    examples_root = os.path.join(REPO, "examples")
    n_cov = 0
    for manifest_path in _find_manifests(examples_root):
        bundle = Bundle.load(manifest_path)
        cert = bundle.manifest.get("certification", {})
        bundle_id = (
            cert.get("slug")
            or bundle.manifest.get("slug")
            or os.path.relpath(bundle.root, examples_root).replace(os.sep, "-")
        )
        payload = serialize_coverage(bundle.coverage())
        with open(
            os.path.join(cov_dir, bundle_id + ".json"),
            "w",
            encoding="utf-8",
            newline="\n",
        ) as fh:
            json.dump(payload, fh, ensure_ascii=False, indent=2, sort_keys=True)
            fh.write("\n")
        n_cov += 1

    print(
        f"Wrote {len(CASES)} case(s) + goldens to {expected_dir}, "
        f"and {n_cov} coverage golden(s) to {cov_dir}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
