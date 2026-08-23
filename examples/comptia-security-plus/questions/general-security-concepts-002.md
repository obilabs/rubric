---
type: SINGLE_CHOICE
domains: [General Security Concepts]
difficulty: EASY
tags: [cryptography, hashing]
explanation: |
  Hashing provides integrity: any change to the input produces a different digest,
  so a matching hash shows the data is unaltered. Hashing is one-way and does not
  provide confidentiality (it isn't reversible to recover the plaintext).
---

# Question

A file is distributed alongside its SHA-256 digest. What security property does
publishing the digest primarily provide?

## Choices

A. Integrity *[CORRECT]*
> Recompute the hash on your copy; if it matches, the file was not tampered with in transit.
B. Confidentiality
> Hashing does not hide the file — anyone can still read it. Confidentiality needs encryption.
C. Availability
> A digest says nothing about whether the file can be reached, only whether it changed.
D. Non-repudiation
> Close, but a bare hash proves nothing about *who* produced it. You need a digital
> signature (hash + private key) for non-repudiation.
