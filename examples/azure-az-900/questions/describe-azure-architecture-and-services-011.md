---
type: DRAG_DROP
domains: ["Describe Azure architecture and services"]
difficulty: EASY
explanation: |
  Azure subscriptions provide a billing boundary and a logical container for resource groups, allowing for organized resource management and billing. Resource groups act as logical containers for Azure resources that share a common lifecycle or purpose. Management groups allow for hierarchical organization and governance of multiple subscriptions, enabling policy application at a broader scope.
---

# Question

Match each Azure organizational component to its primary description or function.

## Draggables

- Subscription
- Resource Group
- Management Group

## Dropzones

- A logical container for resources that share a common lifecycle, deployment, and management.
- A logical container for resource groups, defining a billing boundary and access control scope.
- A hierarchy that allows for centralized governance and management of multiple subscriptions.

## Pairs

- Subscription -> A logical container for resource groups, defining a billing boundary and access control scope.
> Subscriptions serve as a fundamental unit of organization in Azure, defining a billing unit and a scope for policies and access control.
- Resource Group -> A logical container for resources that share a common lifecycle, deployment, and management.
> Resource groups are used to group related Azure resources, making it easier to manage, deploy, and monitor them as a single entity.
- Management Group -> A hierarchy that allows for centralized governance and management of multiple subscriptions.
> Management groups provide an organizational hierarchy above subscriptions, enabling consistent policy and access management across multiple subscriptions.
