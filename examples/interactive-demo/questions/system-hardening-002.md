---
type: SIMULATION
domains: [System Hardening]
difficulty: HARD
tags: [firewall, default-deny]
explanation: |
  Set the default policy to deny, then explicitly allow only what's needed
  (established traffic and admin SSH), and finally turn on logging so denied
  traffic is visible. Allowing everything or leaving logging off defeats the
  purpose.
---

# Task

Configure a host firewall with a default-deny posture. Put the steps in the
order you would safely apply them.

## Steps

1. Allow established and related connections
> Do this BEFORE flipping the default to deny, or you cut off your own in-flight
> session and lock yourself out.
2. Allow inbound SSH from the admin subnet only
> Keep a way in, scoped to where admins actually connect from.
3. Set the default inbound policy to DROP
> Now that the exceptions exist, deny everything else by default.
4. Enable logging of dropped packets
> Silent drops are invisible; logging is what makes the firewall auditable.

## Distractors

- Allow all inbound traffic
> The opposite of default-deny — this is not a hardening step.
- Disable the firewall while testing
> A frequent real-world mistake that leaves the host exposed if "temporary" sticks.
