# Roadmap

Rubric today is a **format + parser + coverage tool**. That's the durable core: a
question is a Markdown file, a bank is a git repo, and the syllabus is a checkable
blueprint. Everything below builds on that without changing it.

The ordering reflects one belief: the format only matters if a learner can *feel* the
difference. So the near-term work is about turning a bank into a diagnostic.

## Near term — the playground

An in-browser page where you paste or open a bank and immediately see it rendered,
then take it and get told **which domains to improve**. This is the showcase, and it
directly exercises both of Rubric's differentiators:

- **Render the per-choice rationale** — after you answer, you see the explanation for
  the option *you* picked, not a generic "the answer is A."
- **Diagnose by domain** — your results are scored against the bundle blueprint, so the
  output is "you're solid on Algebra, thin on Geometry — here's where to drill," the
  same weighting `rubric blueprint` reports for authors.

**The honest blocker:** the parser is Python, and a zero-backend playground wants to
run in the browser. Two ways through, to be decided:

1. Serve the existing Python parser behind a tiny `/validate` API (fastest; needs a host).
2. Port the parser to JS/WASM so the page is fully static (more work; no backend, easy
   to embed anywhere — including a GitHub Pages demo).

A JS/WASM port is a great, self-contained contribution if someone wants to take it.

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

- [ ] `DRAG_DROP` — a real parser for the `DRAGGABLE` / `DROPZONES` / `PAIRS` syntax.
- [ ] `SIMULATION` — task-sequence questions.
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

Have an exam you'd model well, or want to take the JS/WASM port? Open an issue — those
two are the highest-leverage places to help.
