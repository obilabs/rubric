---
type: SIMULATION
domains: ["Describe Azure management and governance"]
difficulty: HARD
explanation: |
  Azure Cost Management + Billing allows you to set budgets to track and control your cloud spending. Budgets can have alert conditions that notify stakeholders when a certain percentage of the budget is consumed, helping to prevent unexpected overspending.
---

# Task

Your team needs to monitor the monthly spending for your Azure subscription, `Contoso-Dev-Subscription`. You must set up a budget of $500 per month and receive an email notification when 80% of the budget is consumed.

## Steps

1. In the Azure portal, search for and select "Cost Management + Billing".
> This is the central hub for managing all aspects of Azure costs and billing.
2. In the left-hand menu, under "Cost Management", select "Budgets".
> This section is specifically for creating and managing spending budgets.
3. Click "+ Add" to create a new budget.
> This initiates the budget creation wizard.
4. On the "Create budget" blade, ensure the "Scope" is set to your `Contoso-Dev-Subscription`. Provide a "Budget name" (e.g., `Dev-Subscription-Monthly-Budget`), set the "Reset period" to "Monthly", "Creation date" to the current month, and "Expiration date" to a future date as needed. Set the "Budget amount" to `500`.
> These settings define the fundamental parameters of your budget, including its scope, frequency, and total allowance.
5. Under "Alert conditions", click "+ Add". Configure the alert: set "Condition" to "Actual cost", "Operator" to "Greater than or equal to", and "Value" to `80`.
> This sets the threshold at which the alert will trigger based on the actual expenditure.
6. Under "Alert details" for the newly added alert condition, enter the email address(es) where notifications should be sent.
> This specifies who will receive the email notification when the budget threshold is met.
7. Click "Create" to finalize and activate the budget with its alert.
> This saves the budget configuration, and it will begin monitoring your subscription's spending.

## Distractors

- Create an Azure Monitor alert rule to track subscription spending.
> Azure Monitor can track metrics, but Azure Cost Management + Billing's "Budgets" feature is specifically designed for cost thresholds and notifications.
- Apply an Azure Policy to restrict resource deployment if costs exceed $500.
> While policies can control resource deployment, setting a budget with alerts is the direct method for *monitoring* and *notifying* about cost consumption, not necessarily preventing deployment.
- Manually review the "Cost analysis" blade daily to track spending.
> The task requires an *automated* notification system when 80% of the budget is consumed, which manual review does not provide.
