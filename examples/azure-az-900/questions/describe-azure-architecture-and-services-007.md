---
type: DRAG_DROP
domains: ["Describe Azure architecture and services"]
difficulty: MEDIUM
explanation: |
  Azure's management hierarchy allows for organizing resources and applying governance at various scopes. Management groups offer enterprise-scale governance, subscriptions manage billing and access, and resource groups logically group related resources.
---

# Question

Match each description of an Azure management scope to its correct term.

## Draggables

- Apply policies and compliance across multiple subscriptions
- Unit for billing and access control for Azure resources
- Logical container for related Azure resources within a subscription

## Dropzones

- Management Group
- Subscription
- Resource Group

## Pairs

- Apply policies and compliance across multiple subscriptions -> Management Group
> Management Groups provide a level of scope above subscriptions, enabling you to organize subscriptions into containers and apply governance policies at scale.
- Unit for billing and access control for Azure resources -> Subscription
> An Azure Subscription is a logical container that provides a boundary for billing and serves as the primary unit for applying Azure role-based access control (RBAC).
- Logical container for related Azure resources within a subscription -> Resource Group
> A Resource Group is a logical container that holds related Azure resources for an application or project, allowing them to be managed as a single unit.
