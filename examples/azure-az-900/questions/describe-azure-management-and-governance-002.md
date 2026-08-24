---
type: SIMULATION
domains: ["Describe Azure management and governance"]
difficulty: MEDIUM
explanation: |
  Azure Policy is the correct service for enforcing organizational standards like allowed locations. The "Allowed locations" built-in policy can be assigned to a scope (like a subscription) and configured with specific regions to ensure compliance for all new resource deployments.
---

# Task

Your organization requires that all new Virtual Machines created in a specific subscription must be deployed to the "East US" region to comply with data residency rules. Create an Azure Policy assignment to enforce this rule.

## Steps

1. In the Azure portal, search for and select "Policy".
> This is the entry point for managing Azure Policy.
2. Under "Authoring" in the left-hand menu, select "Assignments".
> Policy assignments are where you apply policy definitions to a specific scope.
3. Click "+ Assign policy".
> This starts the process of creating a new policy assignment.
4. On the "Basics" tab, select the Scope (your subscription), then click the ellipsis next to "Policy definition" and search for "Allowed locations". Select the built-in policy definition "Allowed locations" and click "Select".
> The "Allowed locations" built-in policy is specifically designed for this purpose, providing a quick way to enforce geographical constraints.
5. On the "Parameters" tab, uncheck "Only show parameters that need input or review", then select "East US" from the "Allowed locations" dropdown.
> This configures the policy to specifically allow only the "East US" region for resource deployments.
6. Review the settings and click "Review + create", then "Create".
> This finalizes the policy assignment, enforcing the rule across the specified scope.

## Distractors

- Creating a custom role-based access control (RBAC) role to restrict VM deployment locations.
> RBAC is used for controlling *who* can do *what* to resources, not *where* resources can be deployed. Azure Policy is the correct tool for enforcing organizational standards like allowed locations.
- Manually instructing users to only deploy VMs in East US.
> Manual instructions rely on human compliance and are not a scalable or enforceable solution for ensuring adherence to organizational standards. Azure Policy provides automated enforcement.
