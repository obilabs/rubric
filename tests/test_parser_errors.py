"""Negative-path and normalization tests for the parser.

These exercise the reject/warn branches that the happy-path suite in
test_parser.py never reaches, plus the two behaviors fixed after the pre-launch
review: TRUE_FALSE correct-answer validation and invalid-difficulty normalization.
"""

import pytest
from rubric import validate_dsl


# ---- frontmatter / type errors --------------------------------------------

def test_invalid_type_rejected():
    result = validate_dsl("---\ntype: BOGUS_TYPE\n---\n# Question\nx\n")
    assert result.success is False
    assert any("Invalid type" in e.message for e in result.errors)


def test_frontmatter_not_a_dict_rejected():
    result = validate_dsl("---\njust a bare string\n---\n# Question\nx\n")
    assert result.success is False
    assert any("dictionary" in e.message.lower() for e in result.errors)


def test_invalid_yaml_rejected():
    # An unclosed flow sequence in the frontmatter raises a YAML error.
    result = validate_dsl("---\ntype: SINGLE_CHOICE\nbad: [1, 2\n---\n# Question\nx\n")
    assert result.success is False
    assert any("yaml" in e.message.lower() for e in result.errors)


# ---- missing section errors -----------------------------------------------

def test_missing_question_section():
    dsl = "---\ntype: SINGLE_CHOICE\n---\n## Choices\nA. x *[CORRECT]*\n"
    result = validate_dsl(dsl)
    assert result.success is False
    assert any("# Question" in e.message for e in result.errors)


def test_missing_choices_section():
    dsl = "---\ntype: SINGLE_CHOICE\n---\n# Question\nWhat is x?\n"
    result = validate_dsl(dsl)
    assert result.success is False
    assert any("## Choices" in e.message for e in result.errors)


# ---- correct-answer count validation --------------------------------------

def test_multiple_select_too_few_correct():
    dsl = (
        "---\ntype: MULTIPLE_SELECT\n---\n# Question\nPick.\n"
        "## Choices\nA. x *[CORRECT]*\nB. y\n"
    )
    result = validate_dsl(dsl)
    assert result.success is False
    assert any("at least 2 correct" in e.message for e in result.errors)


def test_true_false_wrong_choice_count():
    dsl = (
        "---\ntype: TRUE_FALSE\n---\n# Question\nq\n"
        "## Choices\nT. TRUE *[CORRECT]*\nF. FALSE\nM. MAYBE\n"
    )
    result = validate_dsl(dsl)
    assert result.success is False
    assert any("exactly 2 choices" in e.message for e in result.errors)


def test_true_false_no_correct_answer():
    """Regression: a TRUE_FALSE with 2 choices but no *[CORRECT]* must fail."""
    dsl = "---\ntype: TRUE_FALSE\n---\n# Question\nq\n## Choices\nT. TRUE\nF. FALSE\n"
    result = validate_dsl(dsl)
    assert result.success is False
    assert any("exactly 1 correct" in e.message for e in result.errors)


# ---- HOTSPOT error branches -----------------------------------------------

def test_hotspot_invalid_json():
    dsl = (
        "---\ntype: HOTSPOT\n---\n# Question\nClick.\n## Hotspots\n"
        "```json\n{ not valid json }\n```\n"
    )
    result = validate_dsl(dsl)
    assert result.success is False
    assert any("Invalid JSON" in e.message for e in result.errors)


def test_hotspot_missing_json_block():
    dsl = "---\ntype: HOTSPOT\n---\n# Question\nClick.\n"
    result = validate_dsl(dsl)
    assert result.success is False
    assert any("Missing hotspot data" in e.message for e in result.errors)


# ---- CASE_STUDY sub-question error -----------------------------------------

def test_case_study_subquestion_missing_choices():
    dsl = (
        "---\ntype: CASE_STUDY\n---\n# Scenario\nA scenario.\n"
        "## Question 1\nWhat now?\n"
    )
    result = validate_dsl(dsl)
    assert result.success is False
    assert any("### Choices" in e.message and "Question 1" in e.message for e in result.errors)


# ---- warnings --------------------------------------------------------------

def test_rationale_before_any_choice_warns():
    dsl = (
        "---\ntype: SINGLE_CHOICE\n---\n# Question\nq\n"
        "## Choices\n> orphan rationale\nA. x *[CORRECT]*\nB. y\n"
    )
    result = validate_dsl(dsl)
    assert result.success is True  # warning only, not fatal
    assert any("before any choice" in w.message for w in result.warnings)


def test_invalid_difficulty_normalized_to_medium():
    """Fixed: an invalid difficulty warns AND normalizes to MEDIUM in the output."""
    dsl = (
        "---\ntype: SINGLE_CHOICE\ndifficulty: TRIVIAL\n---\n# Question\nq\n"
        "## Choices\nA. x *[CORRECT]*\nB. y\n"
    )
    result = validate_dsl(dsl)
    assert result.success is True
    assert len(result.warnings) > 0
    assert result.data["difficulty"] == "MEDIUM"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
