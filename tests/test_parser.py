"""Tests for the Rubric DSL parser (ported from the original exam-prep engine)."""

import pytest
from rubric import QuestionDSLParser, validate_dsl


# Sample valid DSL
VALID_MULTIPLE_CHOICE = """---
type: MULTIPLE_CHOICE
domains: [Security Operations, Network Security]
difficulty: MEDIUM
tags: [firewall, networking]
explanation: |
  The firewall default deny rule blocks all traffic unless explicitly allowed.
  This is a security best practice.
---

# Question

A security analyst notices that users cannot access the internet after a firewall update.
Which of the following is the MOST likely cause?

[IMAGE: firewall-config]

## Choices

A. The firewall is blocking HTTPS traffic
B. The DNS server is misconfigured
C. The default deny rule was applied *[CORRECT]*
D. The routing table is incorrect
"""

VALID_MULTIPLE_SELECT = """---
type: MULTIPLE_SELECT
domains: [Security Fundamentals]
difficulty: EASY
---

# Question

Which of the following are components of the CIA triad? *(Select TWO)*

## Choices

A. Confidentiality *[CORRECT]*
B. Compliance
C. Integrity *[CORRECT]*
D. Authorization
E. Availability
"""

VALID_HOTSPOT = """---
type: HOTSPOT
domains: [Network Security]
difficulty: HARD
---

# Question

Click on the firewall interface that is configured for the DMZ network.

[IMAGE: network-diagram]

## Hotspots

```json
{
  "image": "network-diagram.png",
  "correctRegions": [
    {"x": 250, "y": 180, "width": 100, "height": 50, "label": "DMZ Interface"}
  ],
  "distractorRegions": [
    {"x": 250, "y": 80, "width": 100, "height": 50, "label": "WAN Interface"}
  ]
}
```
"""

VALID_TRUE_FALSE = """---
type: TRUE_FALSE
domains: [Security Fundamentals]
difficulty: EASY
tags: [encryption, https]
explanation: |
  HTTPS (HTTP Secure) encrypts data in transit using TLS/SSL protocols,
  protecting against eavesdropping and man-in-the-middle attacks.
---

# Question

HTTPS provides encryption for data transmitted between a web browser and server.

## Choices

T. TRUE *[CORRECT]*
F. FALSE
"""

VALID_CASE_STUDY = """---
type: CASE_STUDY
domains: [Security Operations, Incident Response]
difficulty: HARD
tags: [data-breach, incident-response]
---

# Scenario

Your organization experienced a data breach when an S3 bucket containing customer PII was
publicly exposed for 48 hours. The bucket has since been secured, but customer data may
have been accessed by unauthorized parties.

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
Once the threat is contained, notification and remediation can proceed.

## Question 2

Which TWO actions should be included in the remediation plan?

### Choices

A. Review and strengthen IAM policies *[CORRECT]*
B. Delete the AWS account
C. Implement comprehensive logging *[CORRECT]*
D. Disable all S3 services
E. Increase storage capacity

### Explanation

Strengthening IAM policies and implementing logging address the root causes and
prevent similar incidents. Deleting the account or disabling services is too extreme.
"""

VALID_SINGLE_CHOICE = """---
type: SINGLE_CHOICE
domains: [Security Fundamentals]
difficulty: EASY
explanation: Encryption converts plaintext to ciphertext using an algorithm and key.
---

# Question

What is the primary purpose of encryption?

## Choices

A. To make data unreadable to unauthorized users *[CORRECT]*
B. To compress data
C. To delete data
D. To backup data
"""

# A question that uses the per-choice rationale — the teaching payload that is
# Rubric's reason to exist. Each distractor names the misconception behind it.
VALID_WITH_RATIONALE = """---
type: SINGLE_CHOICE
domains: [Algebraic Processes]
difficulty: EASY
explanation: Combine like terms.
---

# Question

Simplify: 15 x 200.

## Choices

A. 3,000 *[CORRECT]*
> 15 x 200 = 3000.
B. 2,500
> Subtracts instead of multiplying.
C. 30,000
> Off by a factor of ten — an extra zero.
"""

# Invalid DSL samples
INVALID_NO_FRONTMATTER = """
# Question
This has no frontmatter

## Choices
A. Option A
"""

INVALID_NO_TYPE = """---
difficulty: MEDIUM
---

# Question
Missing type field
"""

INVALID_WRONG_ANSWER_COUNT = """---
type: MULTIPLE_CHOICE
---

# Question
Multiple choice with 2 correct answers

## Choices
A. Answer A *[CORRECT]*
B. Answer B *[CORRECT]*
C. Answer C
"""


class TestQuestionDSLParser:
    """Test DSL Parser functionality."""

    def test_parse_valid_multiple_choice(self):
        """Test parsing valid MULTIPLE_CHOICE question."""
        parser = QuestionDSLParser()
        result = parser.parse(VALID_MULTIPLE_CHOICE)

        assert result.success is True
        assert len(result.errors) == 0
        assert result.data is not None

        data = result.data
        assert data['type'] == 'MULTIPLE_CHOICE'
        assert data['difficulty'] == 'MEDIUM'
        assert 'Security Operations' in data['domains']
        assert 'firewall' in data['tags']
        assert 'firewall update' in data['question_text']
        assert len(data['choices']) == 4
        assert data['explanation'] != ''

        # Check correct answer
        correct_choices = [c for c in data['choices'] if c['is_correct']]
        assert len(correct_choices) == 1
        assert correct_choices[0]['letter'] == 'C'

    def test_parse_valid_multiple_select(self):
        """Test parsing valid MULTIPLE_SELECT question."""
        result = validate_dsl(VALID_MULTIPLE_SELECT)

        assert result.success is True
        data = result.data
        assert data['type'] == 'MULTIPLE_SELECT'

        # Check multiple correct answers
        correct_choices = [c for c in data['choices'] if c['is_correct']]
        assert len(correct_choices) == 2
        assert 'A' in [c['letter'] for c in correct_choices]
        assert 'C' in [c['letter'] for c in correct_choices]

    def test_parse_valid_hotspot(self):
        """Test parsing valid HOTSPOT question."""
        result = validate_dsl(VALID_HOTSPOT)

        assert result.success is True
        data = result.data
        assert data['type'] == 'HOTSPOT'
        assert 'question_data' in data
        assert 'correctRegions' in data['question_data']
        assert len(data['question_data']['correctRegions']) == 1

    def test_invalid_no_frontmatter(self):
        """Test parsing DSL without frontmatter."""
        result = validate_dsl(INVALID_NO_FRONTMATTER)

        assert result.success is False
        assert len(result.errors) > 0
        assert 'frontmatter' in result.errors[0].message.lower()

    def test_invalid_no_type(self):
        """Test parsing DSL without type field."""
        result = validate_dsl(INVALID_NO_TYPE)

        assert result.success is False
        assert any('type' in err.message.lower() for err in result.errors)

    def test_invalid_wrong_answer_count(self):
        """Test parsing MULTIPLE_CHOICE with wrong answer count."""
        result = validate_dsl(INVALID_WRONG_ANSWER_COUNT)

        assert result.success is False
        assert any('exactly 1 correct answer' in err.message for err in result.errors)

    def test_parse_with_images(self):
        """Test parsing questions with image references."""
        result = validate_dsl(VALID_MULTIPLE_CHOICE)

        assert result.success is True
        assert '[IMAGE: firewall-config]' in result.data['question_text']

    def test_parse_explanation(self):
        """Test parsing explanation field."""
        result = validate_dsl(VALID_MULTIPLE_CHOICE)

        assert result.success is True
        assert result.data['explanation'] != ''
        assert 'default deny rule' in result.data['explanation']

    def test_validation_warnings(self):
        """Test that parser generates warnings for non-critical issues."""
        dsl = """---
type: MULTIPLE_CHOICE
difficulty: SUPER_HARD
---

# Question
Question text

## Choices
A. Answer *[CORRECT]*
"""
        result = validate_dsl(dsl)

        # Should succeed but with warning about invalid difficulty
        assert result.success is True
        assert len(result.warnings) > 0

    def test_parse_valid_true_false(self):
        """Test parsing valid TRUE_FALSE question."""
        result = validate_dsl(VALID_TRUE_FALSE)

        assert result.success is True
        data = result.data
        assert data['type'] == 'TRUE_FALSE'
        assert len(data['choices']) == 2

        # Check correct answer
        correct_choices = [c for c in data['choices'] if c['is_correct']]
        assert len(correct_choices) == 1
        assert 'HTTPS' in data['question_text']  # Check question content
        assert correct_choices[0]['text'] == 'TRUE'

    def test_parse_valid_case_study(self):
        """Test parsing valid CASE_STUDY question."""
        result = validate_dsl(VALID_CASE_STUDY)

        assert result.success is True
        data = result.data
        assert data['type'] == 'CASE_STUDY'
        assert 'S3 bucket' in data['question_text']  # Scenario text
        assert len(data['choices']) == 0  # Case study parent has no choices
        assert 'sub_questions' in data
        assert len(data['sub_questions']) == 2

        # Check first sub-question (single choice)
        sub_q1 = data['sub_questions'][0]
        assert sub_q1['question_number'] == 1
        assert sub_q1['question_type'] == 'SINGLE_CHOICE'
        assert len(sub_q1['choices']) == 4
        assert 'FIRST priority' in sub_q1['question_text']
        correct = [c for c in sub_q1['choices'] if c['is_correct']]
        assert len(correct) == 1
        assert correct[0]['letter'] == 'B'
        assert 'Isolation prevents' in sub_q1['explanation']

        # Check second sub-question (multiple select)
        sub_q2 = data['sub_questions'][1]
        assert sub_q2['question_number'] == 2
        assert sub_q2['question_type'] == 'MULTIPLE_SELECT'
        assert len(sub_q2['choices']) == 5
        assert 'TWO actions' in sub_q2['question_text']
        correct = [c for c in sub_q2['choices'] if c['is_correct']]
        assert len(correct) == 2
        assert set([c['letter'] for c in correct]) == {'A', 'C'}
        assert sub_q2['correct_count'] == 2

    def test_parse_valid_single_choice(self):
        """Test parsing valid SINGLE_CHOICE question."""
        result = validate_dsl(VALID_SINGLE_CHOICE)

        assert result.success is True
        data = result.data
        assert data['type'] == 'SINGLE_CHOICE'
        assert len(data['choices']) == 4

        # Check correct answer
        correct_choices = [c for c in data['choices'] if c['is_correct']]
        assert len(correct_choices) == 1
        assert correct_choices[0]['letter'] == 'A'

    def test_multiple_select_has_correct_count(self):
        """Test that MULTIPLE_SELECT includes correct_count field."""
        result = validate_dsl(VALID_MULTIPLE_SELECT)

        assert result.success is True
        data = result.data
        assert 'correct_count' in data
        assert data['correct_count'] == 2

    def test_case_study_validation_no_sub_questions(self):
        """Test case study validation with no sub-questions."""
        dsl = """---
type: CASE_STUDY
---

# Scenario

This is a scenario with no sub-questions.
"""
        result = validate_dsl(dsl)

        assert result.success is False
        assert any('at least one sub-question' in err.message for err in result.errors)


class TestPerChoiceRationale:
    """The per-choice rationale is Rubric's differentiator — lock its behaviour."""

    def test_rationale_attaches_to_each_choice(self):
        result = validate_dsl(VALID_WITH_RATIONALE)
        assert result.success is True
        by_letter = {c['letter']: c for c in result.data['choices']}
        assert by_letter['A']['rationale'] == '15 x 200 = 3000.'
        assert by_letter['B']['rationale'] == 'Subtracts instead of multiplying.'
        assert 'factor of ten' in by_letter['C']['rationale']

    def test_rationale_is_optional(self):
        """A question with no rationale lines still parses, with rationale None."""
        result = validate_dsl(VALID_SINGLE_CHOICE)
        assert result.success is True
        assert all(c['rationale'] is None for c in result.data['choices'])


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
