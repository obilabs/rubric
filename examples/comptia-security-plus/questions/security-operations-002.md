---
type: SINGLE_CHOICE
domains: [Security Operations]
difficulty: HARD
tags: [incident-response, containment]
explanation: |
  The incident-response order is prepare, identify, contain, eradicate, recover,
  lessons learned. Once an incident is confirmed, containment (isolation) is the
  priority so damage stops spreading before eradication and notification.
---

# Question

A server is confirmed to be actively exfiltrating data to an external host. What should
the responder do FIRST?

## Choices

A. Isolate the affected server from the network *[CORRECT]*
> Containment stops the bleeding. Isolation halts the exfiltration immediately while
> preserving the host for investigation.
B. Rebuild the server from a known-good image
> That is eradication/recovery — valuable, but doing it first destroys evidence and
> may not stop a second compromised host.
C. Notify all customers of a breach
> Notification matters, but jumping to it before containment lets data keep leaving and
> may be premature before scope is known.
D. Run a full antivirus scan
> Scanning a still-connected, actively-compromised host wastes time and lets exfiltration
> continue; contain first, analyze second.
