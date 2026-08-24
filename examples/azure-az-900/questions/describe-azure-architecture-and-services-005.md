---
type: DRAG_DROP
domains: ["Describe Azure architecture and services"]
difficulty: MEDIUM
explanation: |
  Availability Zones provide physical separation within a region, offering independent power, cooling, and networking. Region pairs ensure data residency and help with disaster recovery by allowing updates to be rolled out sequentially. Resource groups serve as a management scope for resources, allowing for policy application and monitoring.
---

# Question

Match each Azure architectural concept to its specific characteristic or benefit.

## Draggables

- Offers protection against datacenter failures within a region
- Ensures data residency and sequential updates for disaster recovery
- Provides a scope for applying policies, access control, and monitoring

## Dropzones

- Availability Zone
- Region Pair
- Resource Group

## Pairs

- Offers protection against datacenter failures within a region -> Availability Zone
> Availability Zones are physically separate locations within an Azure region, each with independent power, cooling, and networking, providing protection against datacenter-level failures.
- Ensures data residency and sequential updates for disaster recovery -> Region Pair
> Azure Region Pairs ensure that one region is updated at a time, minimizing downtime during updates, and they maintain data residency within a geographical boundary for compliance.
- Provides a scope for applying policies, access control, and monitoring -> Resource Group
> Resource groups are logical containers where Azure resources are deployed and managed, allowing for unified application of policies, role-based access control (RBAC), and monitoring.
