---
type: DRAG_DROP
domains: [Ports and Protocols]
difficulty: MEDIUM
tags: [ports, services]
explanation: |
  FTP control is 21, SMTP is 25, RDP is 3389, and NTP is 123.
---

# Question

Match each service to the default port an administrator would open for it.

## Draggables

- FTP (control)
- SMTP
- RDP
- NTP

## Dropzones

- 21
- 25
- 3389
- 123

## Pairs

- FTP (control) -> 21
> FTP uses 21 for control and 20 for data — the control channel is what you open first.
- SMTP -> 25
> Mail transfer between servers. Submission from clients often uses 587 instead.
- RDP -> 3389
> Remote Desktop. Exposing 3389 to the internet is a frequent breach vector.
- NTP -> 123
> Time synchronisation. Wrong clocks break certificate validation and log correlation.
