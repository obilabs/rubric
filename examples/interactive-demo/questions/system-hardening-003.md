---
type: HOTSPOT
domains: [System Hardening]
difficulty: EASY
tags: [firewall, perimeter, hotspot]
explanation: |
  Inbound rules belong at the perimeter, on the device that sees traffic first.
  Filtering deeper in the network still lets the packet cross the boundary.
---

# Question

A new rule must block inbound SSH from the internet. Click the device where that rule belongs.

## Hotspots

```json
{
  "image": {
    "src": "data:image/svg+xml;utf8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%20360%22%20font-family%3D%22sans-serif%22%20font-size%3D%2220%22%3E%3Crect%20width%3D%22800%22%20height%3D%22360%22%20fill%3D%22%23f6f7fb%22%2F%3E%3Cellipse%20cx%3D%22110%22%20cy%3D%22180%22%20rx%3D%2280%22%20ry%3D%2250%22%20fill%3D%22%23dbeafe%22%20stroke%3D%22%231d4ed8%22%20stroke-width%3D%223%22%2F%3E%3Ctext%20x%3D%22110%22%20y%3D%22187%22%20text-anchor%3D%22middle%22%3EInternet%3C%2Ftext%3E%3Crect%20x%3D%22260%22%20y%3D%22140%22%20width%3D%22130%22%20height%3D%2280%22%20rx%3D%2210%22%20fill%3D%22%23fee2e2%22%20stroke%3D%22%23b91c1c%22%20stroke-width%3D%223%22%2F%3E%3Ctext%20x%3D%22325%22%20y%3D%22187%22%20text-anchor%3D%22middle%22%3EFirewall%3C%2Ftext%3E%3Crect%20x%3D%22460%22%20y%3D%22140%22%20width%3D%22130%22%20height%3D%2280%22%20rx%3D%2210%22%20fill%3D%22%23e5e7eb%22%20stroke%3D%22%23374151%22%20stroke-width%3D%223%22%2F%3E%3Ctext%20x%3D%22525%22%20y%3D%22187%22%20text-anchor%3D%22middle%22%3ESwitch%3C%2Ftext%3E%3Crect%20x%3D%22640%22%20y%3D%2250%22%20width%3D%22130%22%20height%3D%2270%22%20rx%3D%2210%22%20fill%3D%22%23dcfce7%22%20stroke%3D%22%2315803d%22%20stroke-width%3D%223%22%2F%3E%3Ctext%20x%3D%22705%22%20y%3D%2292%22%20text-anchor%3D%22middle%22%3EServer%3C%2Ftext%3E%3Crect%20x%3D%22640%22%20y%3D%22240%22%20width%3D%22130%22%20height%3D%2270%22%20rx%3D%2210%22%20fill%3D%22%23fef9c3%22%20stroke%3D%22%23a16207%22%20stroke-width%3D%223%22%2F%3E%3Ctext%20x%3D%22705%22%20y%3D%22282%22%20text-anchor%3D%22middle%22%3ELaptop%3C%2Ftext%3E%3Cg%20stroke%3D%22%236b7280%22%20stroke-width%3D%223%22%3E%3Cline%20x1%3D%22190%22%20y1%3D%22180%22%20x2%3D%22260%22%20y2%3D%22180%22%2F%3E%3Cline%20x1%3D%22390%22%20y1%3D%22180%22%20x2%3D%22460%22%20y2%3D%22180%22%2F%3E%3Cline%20x1%3D%22590%22%20y1%3D%22170%22%20x2%3D%22640%22%20y2%3D%2290%22%2F%3E%3Cline%20x1%3D%22590%22%20y1%3D%22190%22%20x2%3D%22640%22%20y2%3D%22270%22%2F%3E%3C%2Fg%3E%3C%2Fsvg%3E",
    "alt": "Network diagram: Internet, firewall, switch, then a server and a laptop"
  },
  "correctRegions": [
    { "x": 0.325, "y": 0.39, "width": 0.1625, "height": 0.222, "label": "Firewall",
      "rationale": "The perimeter firewall is the first device inbound traffic reaches — the only place a block stops it before it touches the LAN." }
  ],
  "distractorRegions": [
    { "x": 0.575, "y": 0.39, "width": 0.1625, "height": 0.222, "label": "Switch",
      "rationale": "A switch forwards frames; it is not where inbound internet traffic is filtered." },
    { "x": 0.8, "y": 0.139, "width": 0.1625, "height": 0.194, "label": "Server",
      "rationale": "A host firewall on the server is defence in depth, but the traffic has already crossed the perimeter." },
    { "x": 0.8, "y": 0.667, "width": 0.1625, "height": 0.194, "label": "Laptop",
      "rationale": "An endpoint rule protects one machine; the requirement is to stop the traffic at the edge." }
  ]
}
```
