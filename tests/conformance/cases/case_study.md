---
type: CASE_STUDY
domains: [Security Operations, Incident Response]
difficulty: HARD
tags: [data-breach, incident-response]
---

# Scenario

Your organization experienced a data breach when an S3 bucket containing customer PII was
publicly exposed for 48 hours.

[IMAGE: incident-timeline]

## Question 1

What should be the FIRST priority in responding to this incident?

### Choices

A. Notify affected customers immediately
B. Isolate the affected S3 bucket *[CORRECT]*
C. Update the incident response plan
D. Conduct a full security audit

### Explanation

Isolation prevents further data exposure and should be the immediate first step.

## Question 2

Which TWO actions should be included in the remediation plan?

### Choices

A. Review and strengthen IAM policies *[CORRECT]*
B. Delete the AWS account
C. Implement comprehensive logging *[CORRECT]*
D. Disable all S3 services
E. Increase storage capacity

### Explanation

Strengthening IAM policies and implementing logging address the root causes.
