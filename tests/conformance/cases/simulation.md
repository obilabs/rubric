---
type: SIMULATION
domains: [System Hardening]
difficulty: HARD
explanation: |
  Order matters: snapshot, then change, then restart.
---

# Task

Harden the SSH server. Put the required steps in the correct order.

## Steps

1. Back up the current sshd_config
> Always snapshot before changing a live service.
2. Set PasswordAuthentication to no
3. Restart the SSH daemon

## Distractors

- Open port 23 for Telnet
> Telnet is plaintext; opening it undoes the hardening.
- Delete all user accounts
