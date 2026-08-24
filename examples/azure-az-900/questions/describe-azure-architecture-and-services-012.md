---
type: DRAG_DROP
domains: ["Describe Azure architecture and services"]
difficulty: MEDIUM
explanation: |
  Azure Virtual Machines provide Infrastructure as a Service (IaaS) for full control over the OS. Azure App Service is a Platform as a Service (PaaS) offering for hosting web applications with minimal infrastructure management. Azure Functions offer serverless compute for event-driven, short-lived tasks. Azure Blob Storage is optimized for storing massive amounts of unstructured data.
---

# Question

Match each core Azure service to the workload or description it best fits.

## Draggables

- Azure Virtual Machines
- Azure App Service
- Azure Functions
- Azure Blob Storage

## Dropzones

- Ideal for hosting web applications, REST APIs, and mobile backends with minimal infrastructure management.
- Best for workloads requiring full control over the operating system, custom software, or specific network configurations.
- Designed for event-driven, serverless execution of small code snippets that respond to triggers without managing servers.
- Optimized for storing massive amounts of unstructured data, such as images, videos, backups, and data lakes.

## Pairs

- Azure Virtual Machines -> Best for workloads requiring full control over the operating system, custom software, or specific network configurations.
> Azure Virtual Machines offer Infrastructure as a Service (IaaS), providing users with maximum control over the compute environment, including the operating system.
- Azure App Service -> Ideal for hosting web applications, REST APIs, and mobile backends with minimal infrastructure management.
> Azure App Service is a Platform as a Service (PaaS) offering that simplifies the deployment and scaling of web applications, allowing developers to focus on code rather than infrastructure.
- Azure Functions -> Designed for event-driven, serverless execution of small code snippets that respond to triggers without managing servers.
> Azure Functions is a serverless compute service, perfect for executing code in response to events (like HTTP requests or database changes) without provisioning or managing servers.
- Azure Blob Storage -> Optimized for storing massive amounts of unstructured data, such as images, videos, backups, and data lakes.
> Azure Blob Storage is a highly scalable and cost-effective object storage solution for unstructured data, widely used for media files, backups, and data archiving.
