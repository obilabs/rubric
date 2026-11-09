# Roadmap

Rubric is a **format + parser + coverage tool**, and that core is **complete for its
purpose**: a question is a Markdown file, a bank is a git repo, the syllabus is a
checkable blueprint, every declared question type parses in two implementations held in
lockstep by a conformance corpus, the CLI emits a versioned machine-readable report, and
a stranger can build a renderer on the JavaScript parser from one page of documentation.
Nothing in the engine is half-finished, and no planned change to the format is pending.

What follows is therefore not a list of gaps. It is a list of **optional conveniences
for adopters** — things that would make Rubric easier to reach from where someone
already is (an LMS, a GUI, a maths-heavy syllabus), none of which the format needs in
order to be used today. They are kept here, in the open, because "we might do this"
is more honest than a tidy page; they are ordered by nothing but usefulness, and an
adopter who needs one should open an issue or send a pull request rather than wait.

The one belief that shaped the ordering: the format only matters if a learner can *feel*
the difference, which is why the diagnostic work came first and is done.

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

Still open here (neither blocks anyone):

- [ ] A GitHub Pages deployment once the repo is public (Actions is ready).
- [ ] Render math (`$…$`) — today it's shown as source; a small KaTeX-free renderer, or
      an opt-in one, would finish the WAEC maths bank's presentation.
- [x] In-browser support for `DRAG_DROP` and `SIMULATION` (both are now answerable in
      the playground, with the same rationale reveal and domain diagnosis).

## Content — more real banks (optional)

The format is domain-agnostic; proving that means shipping banks beyond the seed corpus.

- [ ] **CompTIA** — fill the Security+ SY0-701 starter to its full blueprint weights;
      add A+, Network+.
- [ ] **Microsoft Azure** — AZ-900 fundamentals, then role-based certs, with the
      official domain weightings as the blueprint.
- [ ] Community-contributed bundles for any exam, each carrying an honest provenance
      note (AI-generated vs. authored vs. licensed).

Every bundle is authored the same way, so this is additive and parallelizable.

## Format — every type shipped, two optional extras

- [x] `DRAG_DROP` — real parser for the `## Draggables` / `## Dropzones` / `## Pairs`
      syntax, with per-pair rationale and reference validation. Rendered in the playground.
- [x] `SIMULATION` — task-sequence questions: ordered `## Steps` + optional
      `## Distractors`, with per-item rationale. Rendered in the playground.
- [x] `HOTSPOT` — region contract (rect / polygon / circle, fraction coordinates), validated in
      both parsers, rendered + graded in the playground with per-region rationale.
- [ ] `HOTSPOT` — validate that a relative `image.src` exists in the bundle.
- [ ] Image references: alt-text and URL forms, and a resolver contract for renderers.

## Interop — meet people where they are (optional)

- [ ] Exporters/importers to and from established formats (GIFT, QTI, `text2qti`) so a
      Rubric bank isn't a walled garden — you can move a bank out as easily as in.
- [ ] A bidirectional GUI ↔ DSL editor (author visually, review as text in a PR).

## Tooling

- [x] **Stable machine-readable output** — `rubric validate --json` and
      `rubric blueprint --json` emit a versioned report (`schema_version`), documented
      as a contract in [`docs/JSON-OUTPUT.md`](docs/JSON-OUTPUT.md) and pinned by golden
      fixtures. Human and JSON output are two renderings of one report object, so they
      cannot disagree; exit codes are unchanged.
- [x] **A renderer guide** — [`docs/BUILD-A-RENDERER.md`](docs/BUILD-A-RENDERER.md): the
      object shape for every question type, how to load the parser with no build step,
      how to grade and reveal the per-choice rationale, how to score against the
      blueprint, and a complete copy-pasteable page that runs from `file://`.
- [ ] A pre-commit hook and GitHub Action wrapping `rubric validate` and
      `rubric blueprint --strict`, so a bank's coverage is enforced on every push. The
      commands and exit codes for it already exist; this is a convenience wrapper.

---

Have an exam you'd model well, or want to write a renderer on top of the JS parser?
[`docs/BUILD-A-RENDERER.md`](docs/BUILD-A-RENDERER.md) is the five-minute version of the
second one. Open an issue — a new example bundle and a great question renderer are the
highest-leverage places to help, and every item above is a genuinely open invitation
rather than something being quietly worked on.
