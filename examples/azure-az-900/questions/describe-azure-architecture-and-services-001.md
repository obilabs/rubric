---
type: DRAG_DROP
domains: ["Describe Azure architecture and services"]
difficulty: EASY
explanation: |
  Azure regions are geographic areas containing one or more datacenters. Availability Zones provide fault isolation within a region, consisting of separate datacenters with independent power, cooling, and networking. Region pairs are two regions within the same geography that are paired for data residency and disaster recovery purposes.
---

# Question

Match each Azure architectural component to its primary characteristic or purpose.

## Draggables

- A geographic area containing one or more datacenters
- A physically separate datacenter within an Azure region
- A pair of regions within the same geography for disaster recovery

## Dropzones

- Azure Region
- Availability Zone
- Region Pair

## Pairs

- A geographic area containing one or more datacenters -> Azure Region
> An Azure Region is a set of datacenters deployed within a latency-defined perimeter and connected through a dedicated regional low-latency network.
- A physically separate datacenter within an Azure region -> Availability Zone
> Availability Zones are unique physical locations within an Azure region, providing high availability by isolating failures to a single zone.
- A pair of regions within the same geography for disaster recovery -> Region Pair
> Azure Region Pairs are designed to ensure data residency within the same geography and enable business continuity for disaster recovery scenarios.
