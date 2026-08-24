---
type: SIMULATION
domains: ["Describe Azure management and governance"]
difficulty: MEDIUM
explanation: |
  Role-Based Access Control (RBAC) allows you to grant granular permissions. The "Virtual Machine Contributor" role provides comprehensive management permissions for VMs without granting broader access to other resource types or the resource group itself, making it suitable for managing VMs within a specific scope.
---

# Task

A new team member, John Doe, needs to manage virtual machines (start, stop, resize, delete) within a specific resource group named `WebAppRG` but should not be able to manage other resource types or delete the resource group itself. Grant John Doe the appropriate role using the Azure portal.

## Steps

1. In the Azure portal, navigate to the `WebAppRG` resource group.
> RBAC roles should be assigned at the lowest necessary scope to adhere to the principle of least privilege.
2. In the left-hand menu, select "Access control (IAM)".
> This is the section within a resource group where you manage role assignments.
3. Click "+ Add" and then "Add role assignment".
> This action initiates the process of assigning a new role to a user, group, or service principal.
4. On the "Role" tab, search for and select the "Virtual Machine Contributor" role, then click "Next".
> This role provides comprehensive management permissions for virtual machines without granting broader contributor access to other resource types or the resource group itself, meeting the task's requirements.
5. On the "Members" tab, select "User, group, or service principal", then click "+ Select members" and search for and select "John Doe", then click "Select".
> This specifies the principal who will receive the defined role permissions.
6. Review the assignment details and click "Review + assign", then "Review + assign" again to confirm.
> This completes the role assignment, applying the permissions to John Doe.

## Distractors

- Assigning the "Contributor" role to John Doe for `WebAppRG`.
> The "Contributor" role grants full access to manage all resources within the scope, including deleting the resource group, which violates the requirement that John should *not* be able to delete the resource group.
- Assigning the "Virtual Machine Administrator Login" role to John Doe.
> This role is specifically for logging into Azure VMs using Azure AD credentials, not for managing the lifecycle (start, stop, delete, etc.) of the virtual machines themselves.
