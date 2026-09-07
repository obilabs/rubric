---
type: HOTSPOT
domains: [System Hardening]
difficulty: EASY
explanation: Inbound rules belong at the perimeter.
---

# Question

Click the device where an inbound-block rule belongs.

## Hotspots

```json
{
  "image": {"src": "diagram.svg", "alt": "Network diagram"},
  "correctRegions": [
    {"x": 0.325, "y": 0.39, "width": 0.1625, "height": 0.222, "label": "Firewall", "rationale": "First device inbound traffic reaches."}
  ],
  "distractorRegions": [
    {"cx": 0.65, "cy": 0.5, "r": 0.08, "label": "Switch", "rationale": "Forwards frames; does not filter internet traffic."},
    {"points": [[0.8, 0.14], [0.96, 0.14], [0.96, 0.33], [0.8, 0.33]], "label": "Server"}
  ]
}
```
