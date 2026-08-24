---
type: SIMULATION
domains: ["Describe Azure management and governance"]
difficulty: MEDIUM
explanation: |
  Azure Policy allows you to create, assign, and manage policies that enforce rules and effects over your resources. To enforce a tag on new resources within a resource group, you create a custom policy definition and then assign it to the target scope.
---

# Task

Your organization requires all new virtual machines deployed into the `rg-development` resource group to have a tag named `Environment` with a value of `Dev`. You need to configure Azure Policy to enforce this.

## Steps

1. In the Azure portal, search for and select "Policy".
> This is the entry point for managing Azure Policy definitions and assignments.
2. In the left-hand menu, select "Definitions" under "Authoring", then click "+ Policy definition".
> This allows you to create a new custom policy rule.
3. Configure the policy definition: set "Definition location" to your subscription, provide a "Name" (e.g., `Enforce-Dev-Environment-Tag`), and for the "Policy rule", use a definition that requires the `Environment` tag with a value of `Dev` on virtual machines, with an "effect" of "Deny".
> This step defines the logic of the policy, specifying what resources it applies to, what conditions must be met, and what action to take if conditions are not met.
4. After saving the policy definition, navigate back to "Policy" and select "Assignments" under "Authoring". Click "Assign policy".
> Policy assignments link a policy definition to a specific scope where it will be enforced.
5. On the "Basics" tab, set the "Scope" to the `rg-development` resource group, select the policy definition you just created, and proceed through the remaining tabs (Parameters, Remediation, Review + create) without making changes unless required by specific policy parameters.
> Assigning the policy to the `rg-development` resource group ensures it only applies to resources within that specific resource group.
6. Click "Create" to finalize the policy assignment.
> This activates the policy, and it will now enforce the tag requirement on new virtual machines within the specified scope.

## Distractors

- Create a resource lock on the `rg-development` resource group.
> Resource locks prevent deletion or modification but do not enforce tagging requirements on new resources.
- Use Azure CLI to manually add the `Environment: Dev` tag to each new VM after creation.
> The task asks to *enforce* the tag automatically with Azure Policy, not to manually apply it post-creation.
- Assign the "Contributor" RBAC role to all users for the `rg-development` resource group.
> RBAC controls *who can do what* but does not enforce configuration standards like tagging on resources.
