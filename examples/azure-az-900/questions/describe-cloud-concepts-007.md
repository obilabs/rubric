---
type: SINGLE_CHOICE
domains: ["Describe cloud concepts"]
difficulty: MEDIUM
explanation: |
  In the shared responsibility model for Infrastructure as a Service (IaaS), the cloud provider (Microsoft) is responsible for the physical infrastructure and its security. However, the customer retains responsibility for managing and securing the guest operating system installed on the virtual machines they deploy.
---

# Question

A company uses Azure Virtual Machines (IaaS) to host its critical business applications.

According to the shared responsibility model, which of the following is primarily the *customer's* responsibility when using Azure IaaS?

## Choices

A. Physical security of the Azure data centers
> This option is incorrect because the physical security of the data centers is always the responsibility of Microsoft, the cloud provider.
B. Management of the virtual machine operating system *[CORRECT]*
> For Infrastructure as a Service (IaaS), the customer is responsible for managing the guest operating system, including patching, configuration, and security.
C. Maintenance of the underlying physical server hardware
> This option is incorrect because the cloud provider, Microsoft, is responsible for maintaining the physical server hardware that hosts the virtual machines.
D. Ensuring the availability of the Azure global network
> This option is incorrect because the availability and underlying infrastructure of the Azure global network is the responsibility of Microsoft, the cloud provider.
