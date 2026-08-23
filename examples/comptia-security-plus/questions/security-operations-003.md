---
type: SINGLE_CHOICE
domains: [Security Operations]
difficulty: MEDIUM
tags: [logging, siem, monitoring]
explanation: |
  A SIEM aggregates and correlates logs from many sources to detect patterns a single
  log could not reveal — such as the same source IP failing logins across dozens of
  hosts. Its value is centralized correlation and alerting.
---

# Question

Why would an organization deploy a SIEM rather than rely on logs stored on each
individual server?

## Choices

A. It correlates events across many sources to reveal patterns no single log shows *[CORRECT]*
> A brute-force sweep looks like noise on one host but an obvious campaign once logs
> from all hosts are correlated in one place.
B. It encrypts each server's local disk
> Log correlation is unrelated to disk encryption; a SIEM does not provide at-rest
> encryption for endpoints.
C. It replaces the need for firewalls
> A SIEM observes and alerts; it does not filter traffic. The two are complementary, not
> substitutes.
D. It guarantees logs can never be deleted
> Forwarding aids retention, but "can never be deleted" overstates it — an attacker with
> enough access can still target the pipeline; a SIEM's core value is correlation.
