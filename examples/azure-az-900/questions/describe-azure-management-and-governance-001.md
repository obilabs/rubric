---
type: SIMULATION
domains: ["Describe Azure management and governance"]
difficulty: EASY
explanation: |
  Resource locks prevent accidental deletion or modification of critical Azure resources. The "Delete" lock type specifically prevents resources from being deleted while allowing other operations. Applying it at the resource level provides targeted protection.
---

# Task

Prevent accidental deletion of a critical Azure Storage Account named `prodstorageaccount123` by applying a resource lock using the Azure portal.

## Steps

1. Navigate to the `prodstorageaccount123` Storage Account in the Azure portal.
> You must select the specific resource you intend to lock.
2. In the resource menu, under "Settings", select "Locks".
> This is the section within a resource's settings where resource locks are managed.
3. Click "+ Add" to create a new lock.
> This action initiates the creation of a new resource lock.
4. Provide a name (e.g., `PreventDeleteLock`), select "Delete" as the Lock type, and optionally add notes, then click "OK".
> The "Delete" lock type specifically prevents deletion, meeting the task requirement, while "Read-only" would prevent all modifications.

## Distractors

- Selecting "Read-only" as the Lock type.
> While "Read-only" also prevents deletion, it also prevents any modification to the resource, which might be too restrictive if the storage account needs to be updated. The task specifically asks to prevent *deletion*.
- Applying the lock at the resource group level where the storage account resides.
> Applying a lock at the resource group level would prevent deletion of *all* resources within that group, or even the group itself, which might not be the desired scope for just one critical storage account. The task specifies locking the storage account.
