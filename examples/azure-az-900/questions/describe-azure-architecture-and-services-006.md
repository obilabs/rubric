---
type: DRAG_DROP
domains: ["Describe Azure architecture and services"]
difficulty: EASY
explanation: |
  Azure organizes its global infrastructure into regions, availability zones, and region pairs. Regions are geographic areas, availability zones provide fault isolation within a region, and region pairs offer disaster recovery across distant regions.
---

# Question

Match each description of an Azure architectural component to its correct term.

## Draggables

- Geographic area with multiple datacenters
- Physically separate datacenters within an Azure region
- Logical grouping of two regions for disaster recovery and data residency

## Dropzones

- Azure Region
- Availability Zone
- Azure Region Pair

## Pairs

- Geographic area with multiple datacenters -> Azure Region
> An Azure Region represents a large geographic area that contains multiple datacenters, providing redundancy and proximity to users.
- Physically separate datacenters within an Azure region -> Availability Zone
> Availability Zones are unique physical locations within an Azure region that provide isolation from failures in other zones.
- Logical grouping of two regions for disaster recovery and data residency -> Azure Region Pair
> An Azure Region Pair consists of two regions within the same geography, separated by hundreds of miles, used for disaster recovery and ensuring data residency.
