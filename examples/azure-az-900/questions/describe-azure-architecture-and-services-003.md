---
type: DRAG_DROP
domains: ["Describe Azure architecture and services"]
difficulty: MEDIUM
explanation: |
  Azure Virtual Machines provide IaaS capability for full control over the operating system, suitable for lift-and-shift scenarios. Azure App Service is a PaaS offering for hosting web applications, APIs, and mobile backends with managed infrastructure. Azure Functions is a serverless compute service for event-driven, short-lived tasks without managing servers.
---

# Question

Match each core Azure compute service to the workload it best supports.

## Draggables

- Hosting custom applications requiring operating system-level control
- Developing and deploying web applications with platform management
- Executing small, event-driven code snippets without managing infrastructure

## Dropzones

- Azure Virtual Machines
- Azure App Service
- Azure Functions

## Pairs

- Hosting custom applications requiring operating system-level control -> Azure Virtual Machines
> Azure Virtual Machines offer Infrastructure as a Service (IaaS), giving you full control over the operating system and software, ideal for migrating existing applications.
- Developing and deploying web applications with platform management -> Azure App Service
> Azure App Service is a Platform as a Service (PaaS) offering designed for hosting web applications, REST APIs, and mobile backends with integrated management features.
- Executing small, event-driven code snippets without managing infrastructure -> Azure Functions
> Azure Functions is a serverless compute service that enables you to run event-triggered code without explicitly provisioning or managing servers.
