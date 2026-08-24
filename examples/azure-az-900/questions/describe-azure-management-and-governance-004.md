---
type: SIMULATION
domains: ["Describe Azure management and governance"]
difficulty: HARD
explanation: |
  Ensuring consistent tagging via Azure Policy is foundational for effective cost tracking. Once resources are tagged, Azure Cost Management + Billing can filter and analyze costs based on these tags, providing granular insights into spending by specific categories like 'Environment'.
---

# Task

Your organization wants to track costs associated with the "Development" environment across all resources in a subscription. Implement a solution that ensures all new resources are tagged with an `Environment` tag and then demonstrates how to view these costs in Azure.

## Steps

1. In the Azure portal, search for "Policy" and then select "Assignments" under "Authoring". Click "+ Assign policy".
> Azure Policy is used to enforce organizational standards like mandatory tags.
2. On the "Basics" tab, select your target subscription for the Scope. For the "Policy definition", search for and select the built-in policy "Require a tag and its value on resources", then click "Select".
> This built-in policy is perfect for enforcing the presence and specific value of a tag.
3. On the "Parameters" tab, set "Tag Name" to `Environment` and "Tag Value" to `Development`. Review and click "Review + create", then "Create".
> This configures the policy to ensure all new resources in the subscription are tagged with `Environment: Development`.
4. Deploy a new resource (e.g., a Storage Account) via the portal or CLI within the assigned subscription, ensuring you add the tag `Environment` with value `Development` during creation.
> This step demonstrates compliance with the policy and creates data that can be analyzed for cost.
5. In the Azure portal, search for and select "Cost Management + Billing", then select "Cost analysis" under "Cost Management".
> This is the primary service for analyzing Azure costs, and "Cost analysis" provides detailed breakdown views.
6. Use the "Add filter" option, select "Tag", then choose "Environment" as the tag key and "Development" as the tag value to filter costs specifically for your development resources.
> This demonstrates how to leverage the enforced tag to gain specific cost insights for the 'Development' environment.

## Distractors

- Manually adding tags to resources after deployment without enforcing a policy.
> Manual tagging is prone to errors and inconsistencies, making reliable cost tracking difficult. Azure Policy ensures consistent compliance.
- Only viewing costs at the resource group level without using tags.
> While you can see costs per resource group, this doesn't allow for granular cost breakdown by logical categories like 'Environment' if resources from multiple environments share a resource group. Tags provide this flexibility.
- Using Azure Monitor to track costs.
> Azure Monitor is primarily for collecting and analyzing telemetry data (logs, metrics) for performance and health, not for financial cost management. Azure Cost Management + Billing is the correct service for cost analysis.
