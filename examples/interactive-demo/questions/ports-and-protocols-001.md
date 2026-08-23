---
type: DRAG_DROP
domains: [Ports and Protocols]
difficulty: EASY
tags: [ports, protocols]
explanation: |
  These are the IANA well-known default ports. HTTP is 80, HTTPS is 443,
  SSH is 22, and DNS is 53.
---

# Question

Drag each protocol onto the port it listens on by default.

## Draggables

- HTTP
- HTTPS
- SSH
- DNS

## Dropzones

- 80
- 443
- 22
- 53

## Pairs

- HTTP -> 80
> Unencrypted web traffic. The classic default deny/allow boundary sits above this.
- HTTPS -> 443
> HTTP wrapped in TLS. If you mixed this up with 80, you swapped the encrypted and
> plaintext ports.
- SSH -> 22
> Remote shell. A common trap is 23 (Telnet), the insecure predecessor.
- DNS -> 53
> Name resolution, usually over UDP but also TCP for large responses.
