---
type: DRAG_DROP
domains: ["Describe Azure architecture and services"]
difficulty: MEDIUM
explanation: |
  Management Groups provide a level of scope above subscriptions, allowing for centralized policy and access management across multiple subscriptions. Subscriptions act as a billing boundary and a unit for access control. Resource Groups are logical containers for related Azure resources, enabling them to be managed as a single unit.
---

# Question

Match each Azure organizational construct to its primary purpose or scope.

## Draggables

- A container for applying policies and governance across multiple subscriptions
- A logical unit of Azure services that are billed together
- A container for related resources that share a common lifecycle

## Dropzones

- Management Group
- Subscription
- Resource Group

## Pairs

- A container for applying policies and governance across multiple subscriptions -> Management Group
> Management groups allow you to organize your subscriptions into containers to apply governance conditions, such as policies and access control, at a higher level.
- A logical unit of Azure services that are billed together -> Subscription
> An Azure subscription is a logical container used to provision resources in Azure, acting as a billing boundary and a unit of access control.
- A container for related resources that share a common lifecycle -> Resource Group
> A resource group is a logical container into which Azure resources like web apps, databases, and storage accounts are deployed and managed.
