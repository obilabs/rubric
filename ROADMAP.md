# Roadmap

Rubric today is a **format + parser + coverage tool**. That's the durable core: a
question is a Markdown file, a bank is a git repo, and the syllabus is a checkable
blueprint. Everything below builds on that without changing it.

The ordering reflects one belief: the format only matters if a learner can *feel* the
difference. So the near-term work is about turning a bank into a diagnostic.

## The playground — shipped

[`web/`](web/) is an in-browser page where you take a bank and, after you answer, get
told **which domains to improve**. It's the showcase, and it exercises both of Rubric's
differentiators directly:

- **Per-choice rationale** — after you answer, you see the explanation for the option
  *you* picked, not a generic "the answer is A."
- **Diagnose by domain** — your results are scored against the bundle blueprint, so the
  output is "you're solid on Algebra, thin on Geometry — here's where to drill," the
  same weighting `rubric blueprint` reports for authors.

**The blocker was that the parser is Python and a zero-backend page runs in the browser.
It was resolved by porting** the parser (and the coverage math) to a dependency-free
JavaScript module, [`web/rubric.js`](web/rubric.js) — chosen over a hosted `/validate`
API (a server to maintain) and over a Pyodide/WASM build (a multi-megabyte runtime that
kills embeddability). The page is fully static: it opens from `file://` and drops onto
GitHub Pages with nothing to run.

The risk with a second parser is silent drift from the reference. That's guarded:
[`tests/conformance/`](tests/conformance/) pins a shared corpus of inputs to the golden
output of the **Python** parser, and both a `pytest` suite and a Node suite assert their
implementation reproduces it byte-for-byte, in CI.

Still open here:

- [ ] A GitHub Pages deployment once the repo is public (Actions is ready).
- [ ] Render math (`$…$`) — today it's shown as source; a small KaTeX-free renderer, or
      an opt-in one, would finish the WAEC maths bank's presentation.
- [x] In-browser support for `DRAG_DROP` and `SIMULATION` (both are now answerable in
      the playground, with the same rationale reveal and domain diagnosis).

## Content — more real banks

The format is domain-agnostic; proving that means shipping banks beyond the seed corpus.

- [ ] **CompTIA** — fill the Security+ SY0-701 starter to its full blueprint weights;
      add A+, Network+.
- [ ] **Microsoft Azure** — AZ-900 fundamentals, then role-based certs, with the
      official domain weightings as the blueprint.
- [ ] Community-contributed bundles for any exam, each carrying an honest provenance
      note (AI-generated vs. authored vs. licensed).

Every bundle is authored the same way, so this is additive and parallelizable.

## Format — finish the reserved types

- [x] `DRAG_DROP` — real parser for the `## Draggables` / `## Dropzones` / `## Pairs`
      syntax, with per-pair rationale and reference validation. Rendered in the playground.
- [x] `SIMULATION` — task-sequence questions: ordered `## Steps` + optional
      `## Distractors`, with per-item rationale. Rendered in the playground.
- [ ] `HOTSPOT` — validate that referenced images exist; richer region metadata.
- [ ] Image references: alt-text and URL forms, and a resolver contract for renderers.

## Interop — meet people where they are

- [ ] Exporters/importers to and from established formats (GIFT, QTI, `text2qti`) so a
      Rubric bank isn't a walled garden — you can move a bank out as easily as in.
- [ ] A bidirectional GUI ↔ DSL editor (author visually, review as text in a PR).

## Tooling

- [ ] A pre-commit hook and GitHub Action wrapping `rubric validate` and
      `rubric blueprint --strict`, so a bank's coverage is enforced on every push.
- [ ] Stable machine-readable output (`--json`) from the CLI for custom pipelines.

---

Have an exam you'd model well, or want to write a renderer on top of the JS parser? Open
an issue — a new example bundle and a great question renderer are the highest-leverage
places to help.
