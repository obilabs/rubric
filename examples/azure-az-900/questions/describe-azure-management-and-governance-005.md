---
type: SIMULATION
domains: ["Describe Azure management and governance"]
difficulty: MEDIUM
explanation: |
  A best practice for deploying resources safely and compliantly involves establishing governance policies first, then organizing resources, deploying them, configuring access, and finally applying protective measures. This sequence ensures adherence to standards from the start and protects critical assets.
---

# Task

You are tasked with deploying a new critical application to Azure. To ensure it meets organizational standards for security, governance, and cost management from the outset, outline the correct order of operations for setting up the environment and deploying resources.

## Steps

1. Define and assign Azure Policies (e.g., allowed locations, required tags, allowed resource SKUs) at the subscription or management group level.
> Establishing governance rules first ensures all subsequent deployments comply with organizational standards and prevents non-compliant resources from being created.
2. Create necessary resource groups to logically organize application components.
> Resource groups provide a management boundary for related resources, which is a prerequisite for deploying resources efficiently and managing them as a unit.
3. Deploy the core application resources (e.g., Virtual Machines, App Services, Databases, Storage Accounts) into the designated resource groups.
> Resources must exist before access can be configured for them or advanced protection measures can be applied.
4. Configure Role-Based Access Control (RBAC) for users or groups who need to manage or access the application resources.
> RBAC should be configured after resources are deployed to grant specific permissions to existing resources, adhering to the principle of least privilege.
5. Apply resource locks (e.g., Delete or Read-only) to critical resources or resource groups.
> Resource locks add an extra layer of protection against accidental modification or deletion of important resources, and are best applied after deployment and initial configuration.

## Distractors

- Deploying all application resources before defining any Azure Policies.
> Deploying resources before policies are in place risks creating non-compliant resources that might need to be remediated or redeployed, leading to extra work and potential security/governance gaps.
- Applying resource locks before deploying any resources.
> You cannot apply locks to resources that do not yet exist. Locks are applied to existing resources or resource groups.
- Configuring RBAC roles for users before any resources are deployed.
> While you can define custom roles, assigning permissions to specific resources requires those resources to exist first. Assigning broad permissions at the subscription level without existing resources is generally not best practice for least privilege.
