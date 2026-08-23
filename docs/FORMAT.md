# The Rubric format

A Rubric question is a UTF-8 Markdown file with two parts: a **YAML frontmatter**
block delimited by `---`, and a **Markdown body**. A *bundle* is a directory of
such files plus a `manifest.json`.

This document describes exactly what the parser in this repository accepts. Where a
feature is reserved but not yet fully parsed, it says so.

---

## 1. A single question

```markdown
---
type: SINGLE_CHOICE
domains: [Algebraic Processes]
difficulty: EASY
tags: [simplification]
explanation: |
  Combine like terms: 7x + 2x = 9x and -3y + 5y = 2y.
---

# Question

Simplify: $7x - 3y + 2x + 5y$.

## Choices

A. $9x + 2y$ *[CORRECT]*
B. $9x - 2y$
C. $5x + 8y$
```

### Frontmatter fields

| Field | Required | Notes |
|---|---|---|
| `type` | **yes** | One of the types in §3. Unknown types are a hard error. |
| `domains` | no | List of domain names. Matched by name against a bundle blueprint. Default `[]`. |
| `difficulty` | no | `EASY`, `MEDIUM`, or `HARD`. Anything else is reported as a *warning* and normalized to `MEDIUM`, so `data['difficulty']` is always one of the three. |
| `tags` | no | Free-form list of strings. Default `[]`. |
| `explanation` | no | A whole-question explanation. Use YAML block scalar `|` for multi-line. Default `""`. |

> **YAML gotcha — domain names with commas.** `domains: [Threats, Vulnerabilities, and Mitigations]`
> is YAML flow syntax and parses as **three** separate domains. If a domain name
> contains a comma, quote it: `domains: ["Threats, Vulnerabilities, and Mitigations"]`.
> `rubric blueprint` will flag the split names as `ORPHAN` domains, which is how you
> catch this.

### Body sections

- `# Question` — the prompt. Required for choice questions. Everything up to the next
  `##` heading is the question text (Markdown, math, and image references pass through
  verbatim).
- `## Choices` — the answer options (see §2).
- `[IMAGE: filename]` — an image reference. Passed through as-is today; a renderer
  resolves it. Alt-text and URL forms are reserved.

---

## 2. Choices

Each choice is a line beginning with a capital letter, a dot, and the option text.
The single correct answer (or answers, for `MULTIPLE_SELECT`) is marked `*[CORRECT]*`:

```markdown
## Choices

A. The default deny rule was applied *[CORRECT]*
B. The DNS server is misconfigured
```

The letters are labels, not indices — `T.`/`F.` for true/false is fine.

### Per-choice rationale

A choice may be followed by one or more lines starting with `>`. They attach to the
**preceding** choice as its rationale — why it is right, or which misconception it
represents. Multiple `>` lines are joined with a space. Rationale is entirely optional;
a question without it parses identically, with each choice's `rationale` set to `null`.

```markdown
A. 120 *[CORRECT]*
> (3 ÷ 5) × 200 = 120.
B. 40
> This is one-fifth of 200 — the numerator was ignored.
```

A `>` line before any choice is a warning and is ignored.

---

## 3. Question types

| Type | Body | Validation |
|---|---|---|
| `SINGLE_CHOICE` | `# Question` + `## Choices` | exactly **1** `*[CORRECT]*` |
| `MULTIPLE_CHOICE` | *(deprecated alias of `SINGLE_CHOICE`)* | exactly **1** correct |
| `MULTIPLE_SELECT` | `# Question` + `## Choices` | **2 or more** correct; result carries `correct_count` |
| `TRUE_FALSE` | `# Question` + `## Choices` | exactly **2** choices |
| `CASE_STUDY` | `# Scenario` + repeated `## Question N` (each with `### Choices`, optional `### Explanation`) | at least **1** sub-question |
| `HOTSPOT` | `# Question` + a ` ```json ` block of `correctRegions` / `distractorRegions` | valid JSON |
| `DRAG_DROP` | `# Question` + `## Draggables` + `## Dropzones` + `## Pairs` | each pair resolves to a declared draggable and dropzone |
| `SIMULATION` | `# Task` + ordered `## Steps` (+ optional `## Distractors`) | at least **1** step; order is significant |

A `CASE_STUDY` sub-question is inferred as `MULTIPLE_SELECT` when it has more than one
correct choice, otherwise `SINGLE_CHOICE`.

`MULTIPLE_CHOICE` is validated by the same rules as `SINGLE_CHOICE`, but the parser
does **not** rewrite the type string — a `MULTIPLE_CHOICE` input still reports
`data['type'] == 'MULTIPLE_CHOICE'`. Prefer `SINGLE_CHOICE` in new content.

### DRAG_DROP

A drag-drop question declares the tokens you drag, the targets you drop them on, and
the correct mapping between them:

```markdown
---
type: DRAG_DROP
domains: [Ports and Protocols]
---

# Question

Match each protocol to the port it listens on by default.

## Draggables

- HTTP
- HTTPS
- SSH

## Dropzones

- 80
- 443
- 22

## Pairs

- HTTP -> 80
> Unencrypted web traffic uses port 80.
- HTTPS -> 443
- SSH -> 22
```

- **`## Draggables`** and **`## Dropzones`** are bulleted lists (`-` or `*`). Each is
  required and must be non-empty. Items get ids `d1`, `d2`, … and `z1`, `z2`, … in order,
  for renderers to reference.
- **`## Pairs`** lists the correct mappings, one per line, as `draggable -> dropzone`
  (`->` or the Unicode `→`). Each side must **exactly match** a declared draggable /
  dropzone label — an unknown reference, or a line with no arrow, is an error. Labels
  should be unique within a question so a pair resolves unambiguously.
- A pair may carry a `>` **rationale** line, exactly like a choice — why the mapping is
  right, or which mis-pairing it guards against.
- Draggables not named in any pair are allowed (they act as distractors). A dropzone may
  appear in more than one pair (bucketing).

Parsed `question_data`:

```python
{
  "draggables": [{"id": "d1", "text": "HTTP"}, ...],
  "dropzones":  [{"id": "z1", "text": "80"}, ...],
  "pairs": [
    {"draggable": "HTTP", "dropzone": "80", "rationale": "Unencrypted web traffic..."},
    {"draggable": "HTTPS", "dropzone": "443", "rationale": None},
  ],
}
```

### SIMULATION

A simulation is a **task-sequence**: a task, the ordered steps that solve it, and
optionally the wrong actions offered alongside them.

```markdown
---
type: SIMULATION
domains: [System Hardening]
---

# Task

Harden the SSH server. Put the required steps in the correct order.

## Steps

1. Back up the current sshd_config
> Snapshot before changing a live service.
2. Set PasswordAuthentication to no
3. Restart the SSH daemon

## Distractors

- Open port 23 for Telnet
> Telnet is plaintext; opening it undoes the hardening.
```

- **`# Task`** is the prompt (note: `# Task`, not `# Question`). It becomes
  `question_text`.
- **`## Steps`** is an ordered list (`1.`, `2.`, …) whose **order is the correct
  sequence**. At least one step is required. Steps are numbered by *appearance*, so a
  mis-numbered list (`1.` `1.` `1.`) still yields `1, 2, 3`.
- **`## Distractors`** is an optional bulleted list of wrong actions.
- Any step or distractor may carry a `>` rationale.

Parsed `question_data`:

```python
{
  "steps": [
    {"order": 1, "text": "Back up the current sshd_config", "rationale": "Snapshot..."},
    {"order": 2, "text": "Set PasswordAuthentication to no", "rationale": None},
    ...
  ],
  "distractors": [
    {"text": "Open port 23 for Telnet", "rationale": "Telnet is plaintext..."},
  ],
  "total_steps": 3,
}
```

---

## 4. Parsed output

`validate_dsl(text)` returns a `ParseResult`:

```python
ParseResult(
    success: bool,
    data: dict | None,           # the structured question (below)
    errors: list[ParseError],    # each has .line, .message, .severity
    warnings: list[ParseError],
)
```

On success, `data` for a choice question looks like:

```python
{
  "type": "SINGLE_CHOICE",
  "domains": ["Algebraic Processes"],
  "difficulty": "EASY",
  "tags": ["simplification"],
  "question_text": "Simplify: $7x - 3y + 2x + 5y$.",
  "choices": [
    {"letter": "A", "text": "$9x + 2y$", "is_correct": True,  "rationale": None},
    {"letter": "B", "text": "$9x - 2y$", "is_correct": False, "rationale": None},
  ],
  "explanation": "Combine like terms: ...",
  "question_data": {},
}
```

`CASE_STUDY` adds a `sub_questions` list; `HOTSPOT` puts its regions in
`question_data`; `MULTIPLE_SELECT` adds a top-level `correct_count`.

---

## 5. Bundles and the blueprint

A bundle groups questions and declares the exam's structure. `manifest.json`:

```json
{
  "format": "rubric-bundle/v1",
  "vendor": { "name": "CompTIA", "slug": "comptia" },
  "certification": {
    "name": "CompTIA Security+ (SY0-701)",
    "code": "SY0-701",
    "passing_score": 750
  },
  "domains": [
    { "name": "General Security Concepts", "weight": 12, "order": 1 },
    { "name": "Security Operations",        "weight": 28, "order": 4 }
  ],
  "question_files": [
    "questions/general-security-concepts-001.md",
    "questions/security-operations-001.md"
  ]
}
```

- **`domains[].weight`** is the blueprint: each domain's intended share of the exam.
  `rubric blueprint` compares the actual per-domain question distribution against these
  weights and flags each domain as `ok`, `over`, `under`, `NONE` (declared but empty),
  or `ORPHAN` (questions reference a domain the blueprint never declared).
- **`question_files`** are paths relative to the manifest. Every one must exist, or
  `Bundle.load` raises — a missing file is a structural fault, distinct from a question
  that merely fails to parse.
- `format` should be `rubric-bundle/v1`. The pre-extraction id
  `examgenie-content-bundle/v1` is still accepted with a note.

`Bundle.coverage()` returns the same data programmatically as a list of
`DomainCoverage` rows, so you can gate CI on syllabus coverage however you like.
