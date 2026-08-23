---
type: SIMULATION
domains: [System Hardening]
difficulty: MEDIUM
tags: [ssh, hardening]
explanation: |
  Snapshot first so you can roll back, make the change, then restart the service
  to apply it. Enabling Telnet or deleting accounts are traps, not steps.
---

# Task

Harden an SSH server so it no longer accepts password logins. Put the required
actions in the correct order.

## Steps

1. Back up the current sshd_config
> Always snapshot a live service's config before editing it, so a mistake is a
> one-line rollback rather than an outage.
2. Set PasswordAuthentication to no
> This is the actual hardening change — it forces key-based authentication.
3. Restart the SSH daemon
> Config changes to sshd don't take effect until the daemon reloads.

## Distractors

- Open port 23 for Telnet
> Telnet is unencrypted; enabling it undoes the point of hardening SSH.
- Delete all existing user accounts
> Destructive and unrelated — hardening authentication is not the same as removing users.
