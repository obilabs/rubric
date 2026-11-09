# Machine-readable CLI output

Both `rubric` commands take `--json` and print one JSON object to stdout instead of
the human table:

```bash
rubric validate  --json examples/waec/mathematics/manifest.json
rubric blueprint --json examples/comptia-security-plus/manifest.json
```

The human output and the JSON are two renderings of **the same report object**
(`rubric.report`), so they cannot disagree about what was found. **Exit codes are
identical either way** — `--json` changes what is printed, never the verdict:

| exit | meaning |
|---|---|
| `0` | clean |
| `1` | questions failed to parse, or `blueprint --strict` found a domain needing attention |
| `2` | structural/usage failure — no manifest, no question files |

With `--json`, the structural failure (exit 2) is also a JSON object on **stdout**;
without it, that message goes to stderr as before. So a consumer never has to
parse prose or infer a reason from the exit code alone.

---

## Stability — what this contract promises

Every payload carries `schema_version`, an integer, currently **`1`**.

- **Additive changes do not bump it.** New fields may appear in any release. A
  consumer must ignore fields it does not recognise, and must not assume the key
  set is closed.
- **Anything breaking bumps it**: removing a field, renaming one, changing its
  type, or changing the meaning of an existing value. A bump is announced in
  `ROADMAP.md`, as with a format change.
- Key order is not part of the contract (keys are emitted sorted, but parse the
  JSON — don't diff it as text). Neither is `rubric_version`, which reports the
  installed package and is there for logs.

The shapes below are pinned by golden fixtures in
[`tests/cli_json/`](../tests/cli_json/) and asserted in `tests/test_cli_json.py`,
so a change to this contract cannot land quietly.

Paths in a report are relative to the working directory when the file sits under
it, always with `/` separators — the same string on Windows and Linux, and no
developer's home directory in a CI log.

---

## `rubric validate --json`

One row per question file, plus a summary. `target` echoes the path you asked
about; a `manifest.json` expands to the files it references, a directory to every
`*.md` under it, a file to itself.

```jsonc
{
  "schema_version": 1,
  "rubric_version": "0.1.0",
  "command": "validate",
  "target": "examples/interactive-demo/manifest.json",
  "ok": true,                       // no file failed to parse
  "summary": { "total": 5, "passed": 5, "failed": 0, "warned": 0 },
  "files": [
    {
      "path": "examples/interactive-demo/questions/ports-and-protocols-001.md",
      "status": "pass",             // pass | warn | fail | unreadable
      "errors": [],
      "warnings": []
    }
  ],
  "exit_code": 0
}
```

A failure is *described*, not merely signalled — this is the whole point of the
flag. Errors and warnings are the same object shape (`line`, `message`,
`severity`); `line` is `0` when the problem has no single line to point at:

```jsonc
{
  "path": "tests/cli_json/inputs/broken.md",
  "status": "fail",
  "errors": [
    { "line": 0, "message": "Missing '## Choices' section", "severity": "error" },
    { "line": 0, "message": "SINGLE_CHOICE must have exactly 1 correct answer, found 0",
      "severity": "error" }
  ],
  "warnings": []
}
```

Notes:

- `warnings` are always present in the JSON. `-v` / `--verbose` only controls
  whether the *human* renderer prints them; it does not change the payload.
- `status: "unreadable"` means the file could not be opened at all (permissions, a
  broken link). It counts as a failure, and its single error carries the OS reason.
- `summary.passed` is `total - failed`, so a file that only warns counts as passed
  — the same arithmetic the human summary line prints.

## `rubric blueprint --json`

One row per domain — the blueprint rows first, in declared order, then any
`orphan` domains the questions reference but the manifest never declared.

```jsonc
{
  "schema_version": 1,
  "rubric_version": "0.1.0",
  "command": "blueprint",
  "manifest": "examples/comptia-security-plus/manifest.json",
  "title": "CompTIA Security+ (SY0-701)",
  "format_note": null,              // set when a legacy/unknown manifest format was accepted
  "blueprint_domains": 5,           // domains declared in the manifest
  "strict": true,
  "ok": false,                      // no problems AND nothing failed to parse
  "questions": { "files": 7, "parsed": 7, "failed": 0 },
  "domains": [
    {
      "domain": "General Security Concepts",
      "target_weight": 12.0,        // declared % of the exam, null if undeclared
      "actual_weight": 28.6,        // this domain's % of the parsed bank
      "question_count": 2,
      "delta": 16.6,                // actual - target, percentage points, null if no target
      "in_blueprint": true,
      "status": "over"              // ok | over | under | uncovered | orphan
    },
    {
      "domain": "Security Architecture",
      "target_weight": 18.0,
      "actual_weight": 0.0,
      "question_count": 0,
      "delta": -18.0,
      "in_blueprint": true,
      "status": "uncovered"
    }
  ],
  "problems": 2,                    // rows with status under | uncovered | orphan
  "failures": [],                   // questions that failed to parse: { file, errors: [string] }
  "exit_code": 1                    // 1 here only because --strict was given
}
```

Status values:

| `status` | meaning |
|---|---|
| `ok` | within ±10 percentage points of the declared weight |
| `over` | at least 10 points above it |
| `under` | at least 10 points below it |
| `uncovered` | declared in the blueprint, zero questions |
| `orphan` | questions tag this domain, the blueprint never declared it |

Percentages are computed over **successfully parsed** questions only, which is why
`questions` reports `files`, `parsed` and `failed` separately. `failures[].file`
is relative to the manifest's directory.

## Structural failure (exit 2)

There is no bank to report on, so the payload carries only the reason:

```json
{
  "schema_version": 1,
  "rubric_version": "0.1.0",
  "command": "validate",
  "ok": false,
  "error": "Manifest not found: tests/cli_json/inputs/absent/manifest.json",
  "exit_code": 2
}
```

`error` is present **only** in this form. Distinguish the two cases by its
presence, or by `exit_code`: a bank that loaded but contains a broken question is
the normal `validate` payload with `ok: false`, not this.

---

## Worked pipeline

Gate a bank on coverage without parsing prose — list the thin domains:

```bash
rubric blueprint --json bank/manifest.json > report.json
python - <<'EOF'
import json
report = json.load(open("report.json"))
for d in report["domains"]:
    if d["status"] in ("under", "uncovered", "orphan"):
        print(f'{d["domain"]}: {d["status"]} ({d["delta"]})')
EOF
```

Or, with `jq`, list the files a CI run should point a reviewer at:

```bash
rubric validate --json bank/manifest.json | jq -r '.files[] | select(.status=="fail") | .path'
```

The same report is available in-process, without a subprocess:

```python
from rubric.bundle import Bundle
from rubric.report import build_blueprint_report

report = build_blueprint_report(Bundle.load("bank/manifest.json"), strict=True)
thin = [d["domain"] for d in report["domains"] if d["status"] in ("under", "uncovered")]
```
