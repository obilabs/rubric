---
type: SINGLE_CHOICE
domains: [Security Operations]
difficulty: MEDIUM
tags: [firewall, network]
explanation: |
  An implicit deny (default deny) rule blocks any traffic not explicitly permitted.
  After a firewall change, users losing all internet access points to a rule set that
  no longer allows the previously-permitted outbound traffic.
---

# Question

After a firewall change, users can no longer reach the internet at all. Which is the
MOST likely cause?

## Choices

A. An implicit deny is now blocking previously-allowed traffic *[CORRECT]*
> Firewalls end their rule set with "deny all"; if the allow rules were removed or
> reordered, everything falls through to that deny.
B. The DNS server was upgraded
> A DNS problem breaks name resolution, but users could still reach sites by IP —
> here nothing gets out, which is broader than DNS.
C. HTTPS inspection was disabled
> Disabling inspection would reduce visibility, not block connectivity outright.
D. The routing table gained a new default route
> A new valid default route would restore or change reachability, not cut off all traffic.
