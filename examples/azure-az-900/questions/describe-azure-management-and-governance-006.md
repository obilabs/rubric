---
type: SIMULATION
domains: ["Describe Azure management and governance"]
difficulty: EASY
explanation: |
  Resource locks prevent accidental deletion or modification of Azure resources. The 'CanNotDelete' lock type prevents deletion, while 'ReadOnly' prevents both deletion and modification. You apply them directly to the resource or resource group.
---

# Task

You are an Azure administrator and need to ensure that a critical virtual machine named `vm-prod-web01` in the `rg-prod-web` resource group cannot be accidentally deleted by anyone.

## Steps

1. Navigate to the `rg-prod-web` resource group in the Azure portal.
> Resource locks can be applied at various scopes, and applying it to the resource group will protect all resources within it, including the specified VM.
2. In the left-hand menu of the resource group, select "Locks".
> This section is specifically designed for managing resource locks.
3. Click "+ Add" to create a new lock.
> This action initiates the process of defining a new resource lock.
4. Provide a name for the lock (e.g., `PreventProdWebDeletion`), select "Delete" as the Lock type, and optionally add notes.
> The "Delete" lock type (CanNotDelete) ensures that the resource or any resources within the scope cannot be deleted.
5. Click "OK" to apply the lock.
> This finalizes the creation and application of the resource lock.

## Distractors

- Navigate to Azure Policy and create a new policy definition to deny resource deletion.
> While Azure Policy *can* be used to prevent deletion, a resource lock is a simpler and more direct way to protect specific existing resources from accidental deletion.
- Assign the "Reader" RBAC role to all users for the `rg-prod-web` resource group.
> The "Reader" role only grants read permissions; it does not prevent users with other roles (like Contributor or Owner) from deleting resources.
- Delete the `vm-prod-web01` virtual machine.
> The task is to *prevent* accidental deletion, not to delete the VM.
