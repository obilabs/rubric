---
type: SINGLE_CHOICE
domains: [Report Fixtures]
difficulty: TRICKY
explanation: |
  A valid question whose difficulty is not one of EASY/MEDIUM/HARD, so the
  parser warns and normalises it — the "warn" row in the golden report.
---

# Question

Which status does a question with an unknown difficulty report?

## Choices

A. warn *[CORRECT]*
> The difficulty is normalised to MEDIUM and a warning is attached.
B. fail
> An unknown difficulty is a warning, not an error; the question still parses.
