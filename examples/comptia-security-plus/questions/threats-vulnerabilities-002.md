---
type: SINGLE_CHOICE
domains: ["Threats, Vulnerabilities, and Mitigations"]
difficulty: MEDIUM
tags: [web, injection, mitigation]
explanation: |
  Parameterized queries (prepared statements) separate code from data, so
  attacker-supplied input can never be interpreted as SQL. Input validation helps
  but is defence-in-depth, not the primary fix.
---

# Question

Which control MOST directly prevents SQL injection in a web application?

## Choices

A. Parameterized queries *[CORRECT]*
> The database treats input strictly as a value, never as executable SQL — this closes
> the vulnerability class at its root.
B. A stronger password policy
> Passwords protect authentication; SQL injection abuses how a query is built, regardless
> of how strong any password is.
C. Full-disk encryption
> Encryption at rest protects a stolen disk. The injected query runs against the live,
> decrypted database, so it offers no protection here.
D. A longer session timeout
> Session settings affect how long a login lasts; they have no bearing on how user input
> is concatenated into a query.
