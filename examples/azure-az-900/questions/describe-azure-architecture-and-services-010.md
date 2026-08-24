---
type: DRAG_DROP
domains: ["Describe Azure architecture and services"]
difficulty: HARD
explanation: |
  Choosing the right Azure service depends on specific workload requirements. App Service is ideal for web apps with minimal infrastructure management, Blob Storage excels at cost-effective unstructured data storage, and Functions are perfect for event-driven serverless tasks. Virtual Machines provide the highest level of control when specific OS requirements exist.
---

# Question

Match each workload description to the most appropriate Azure service.

## Draggables

- Hosting a traditional ASP.NET web application with minimal infrastructure management
- Storing petabytes of unstructured data for archives and backups
- Executing short-lived, event-driven code snippets without provisioning servers
- Requiring full administrative control over the operating system for custom software

## Dropzones

- Azure App Service
- Azure Blob Storage
- Azure Functions
- Azure Virtual Machines

## Pairs

- Hosting a traditional ASP.NET web application with minimal infrastructure management -> Azure App Service
> Azure App Service is a PaaS offering that provides a fully managed environment for hosting web applications, reducing the operational overhead of managing servers.
- Storing petabytes of unstructured data for archives and backups -> Azure Blob Storage
> Azure Blob Storage is a highly scalable and cost-effective solution for storing large amounts of unstructured data like backup files and archives.
- Executing short-lived, event-driven code snippets without provisioning servers -> Azure Functions
> Azure Functions is a serverless compute service well-suited for event-driven tasks that run for short durations, where you only pay for the execution time.
- Requiring full administrative control over the operating system for custom software -> Azure Virtual Machines
> Azure Virtual Machines provide Infrastructure as a Service (IaaS), allowing users complete control over the operating system and installed software, which is necessary for highly customized environments.
