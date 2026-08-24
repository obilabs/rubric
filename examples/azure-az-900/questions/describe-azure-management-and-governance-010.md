---
type: SIMULATION
domains: ["Describe Azure management and governance"]
difficulty: MEDIUM
explanation: |
  When deploying and securing resources, it's generally best practice to create the logical container (resource group) first, then deploy the resource with initial configurations (like tags), and finally apply protective measures (like resource locks). Tags are best applied during creation for consistency and cost tracking.
---

# Task

You need to deploy a new virtual machine for the IT department, ensure it's tagged correctly, and protect it from accidental deletion. Arrange the following actions in the correct sequence to achieve this goal efficiently.

## Steps

1. Create a new resource group (e.g., `rg-it-vm`) in the desired Azure region.
> Resource groups provide a logical container for related resources, and it's a prerequisite to deploy resources into one.
2. Deploy the new virtual machine to the `rg-it-vm` resource group, ensuring the `Department: IT` tag is applied during the virtual machine creation process.
> Deploying the resource comes after establishing its container. Applying tags during creation ensures immediate compliance and simplifies cost management and organization from the start.
3. Apply a 'CanNotDelete' resource lock to the newly created virtual machine.
> Resource locks are applied *after* a resource exists to protect it from accidental modification or deletion, serving as a governance layer.

## Distractors

- Apply a 'CanNotDelete' resource lock before creating the virtual machine.
> Resource locks can only be applied to existing resources; you cannot lock something that hasn't been created yet.
- Create an Azure Policy to enforce the `Department: IT` tag after the VM is deployed.
> While a policy *could* enforce tags, applying the tag directly during creation is more efficient for a single deployment and ensures the tag is present from the outset, rather than requiring a post-deployment remediation or policy evaluation.
- Assign an RBAC role to a user for the resource group before creating the resource group.
> RBAC roles are assigned to existing scopes (subscriptions, resource groups, or resources). You cannot assign a role to a resource group that does not yet exist.
