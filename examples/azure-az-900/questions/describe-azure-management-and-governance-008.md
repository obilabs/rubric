---
type: SIMULATION
domains: ["Describe Azure management and governance"]
difficulty: MEDIUM
explanation: |
  Role-Based Access Control (RBAC) allows you to manage who has access to Azure resources, what they can do with those resources, and what areas they have access to. Assigning the Contributor role to a specific user on a resource group grants them full access to manage all resources within that group, but not the ability to delegate access to others.
---

# Task

A new developer, `developer@yourcompany.com`, has joined your team and needs the ability to manage all resources within the `rg-webapp-dev` resource group, including creating, modifying, and deleting resources. However, they should not be able to manage user access to the resource group itself.

## Steps

1. In the Azure portal, search for and navigate to the `rg-webapp-dev` resource group.
> RBAC assignments are made at a specific scope, and the resource group is the target scope for this task.
2. In the left-hand menu, select "Access control (IAM)".
> This blade is where all RBAC assignments are managed for the selected scope.
3. Click "+ Add" and then "Add role assignment".
> This action initiates the process of granting a new role to a user, group, or service principal.
4. On the "Role" tab, select the "Contributor" role.
> The Contributor role allows managing all resources but not delegating access, which aligns with the requirements.
5. On the "Members" tab, select "User, group, or service principal", then click "+ Select members" and search for `developer@yourcompany.com`. Select the user.
> This specifies the identity to whom the role will be assigned.
6. Click "Review + assign" to review the assignment details, then click "Review + assign" again to finalize the role assignment.
> This confirms the role assignment, granting the specified permissions to the developer.

## Distractors

- Assign the "Owner" RBAC role to `developer@yourcompany.com` for the `rg-webapp-dev` resource group.
> The "Owner" role includes the ability to manage access (delegate roles), which the task specifically states the developer should *not* have.
- Apply a resource lock to the `rg-webapp-dev` resource group to restrict changes.
> Resource locks prevent accidental changes or deletion by *anyone* (including the developer), rather than granting specific management permissions to a user.
- Create a new Azure Policy to allow `developer@yourcompany.com` to manage resources.
> Azure Policy enforces rules and standards, but RBAC is the correct mechanism for granting specific users permissions to manage resources.
