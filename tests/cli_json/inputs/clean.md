---
type: TRUE_FALSE
domains: [Report Fixtures]
difficulty: EASY
explanation: |
  A question that parses with no errors and no warnings — the "pass" row in the
  golden report.
---

# Question

A report's `schema_version` is part of the CLI's contract.

## Choices

A. True *[CORRECT]*
> Additive changes keep the version; a breaking change bumps it.
B. False
> The field exists precisely so a consumer can rely on the shape.
