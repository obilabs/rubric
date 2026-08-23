# The Rubric playground

A **fully static, zero-backend** page for the Rubric format. Take a question bank in the
browser and, after you answer, see the two things Rubric is built for: the rationale for
the option *you* picked, and a domain-by-domain diagnosis of what to drill next — scored
against the bank's blueprint, exactly the way `rubric blueprint` scores it for authors.

Everything runs client-side. There is **no build step and no server** — open
`index.html` from `file://`, or serve the folder on any static host (GitHub Pages).

```bash
# from the repo root
cd web
python -m http.server 8099      # then open http://localhost:8099
```

## What's here

| File | Role |
|---|---|
| `index.html` | The playground UI (self-contained: inline CSS + app JS). |
| `rubric.js` | A **dependency-free JavaScript port** of the parser in `src/rubric/parser.py` plus the coverage math from `bundle.py`. Loads as a browser global (`window.Rubric`) and as a Node CommonJS module (for the tests). |
| `examples.bundle.js` | The example banks in `../examples/`, inlined so the page needs zero `fetch` (works from `file://`). **Generated — do not edit.** |
| `build_examples.cjs` | Regenerates `examples.bundle.js` from `../examples/`. |
| `test/` | Parity tests that prove the JS port matches the Python reference. |

## Why a JavaScript port (and not an API, or WASM)

A zero-backend page has to parse in the browser. The parser is Python, so there were
three ways through:

1. **Host the Python parser behind a `/validate` API** — rejected: a server to run and
   maintain, for a project whose whole pitch is git-native and self-hostable.
2. **Compile Python to WASM (Pyodide)** — rejected: a multi-megabyte runtime download
   defeats "embeddable demo."
3. **Port the parser to plain JavaScript** — chosen: a few hundred lines, no
   dependencies, static-hostable and embeddable anywhere.

The parser's only real dependency was a YAML frontmatter reader; the port hand-parses
the small YAML subset Rubric's frontmatter uses rather than vendoring a full library.

## Keeping the two parsers honest

Two implementations of one grammar can drift apart silently — and "silence that looks
like success" is exactly the failure this project is built to avoid. So the JS port does
not get to disagree with the reference:

- `../tests/conformance/build.py` runs the **Python** parser over a fixed corpus of
  inputs and writes the golden output (`cases/*.md` + `expected/*.json`), plus coverage
  goldens over every example bank (`expected_coverage/*.json`).
- `../tests/test_conformance.py` (pytest) asserts the **Python** parser still reproduces
  those goldens — so they can't rot.
- `test/parity.test.cjs` and `test/coverage_parity.test.cjs` assert the **JavaScript**
  parser reproduces them too, byte-for-byte.

If either side changes behaviour, its test goes red.

```bash
npm test                          # both JS parity suites; no dependencies to install
# and on the Python side:
python -m pytest tests/test_conformance.py
```

After an **intended** parser change, regenerate the corpus and review the diff:

```bash
python tests/conformance/build.py
node web/build_examples.cjs        # if example banks changed
```

## Scope

The playground fully supports the choice-based question types (`SINGLE_CHOICE`,
`MULTIPLE_CHOICE`, `MULTIPLE_SELECT`, `TRUE_FALSE`), which is every question in the
bundled example banks. Math (`$…$`) is shown as source for now. `CASE_STUDY`, `HOTSPOT`,
and the reserved `DRAG_DROP` / `SIMULATION` types parse but are not yet rendered as
interactive items — see [`../ROADMAP.md`](../ROADMAP.md).
