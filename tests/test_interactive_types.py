"""Tests for the interactive question types: DRAG_DROP and SIMULATION.

These were reserved (stub + warning) until real parsers landed. They keep
Rubric's per-item ``>`` rationale — the teaching payload — so the tests lock
both the structure and the rationale behaviour.
"""

import pytest
from rubric import validate_dsl


VALID_DRAG_DROP = """---
type: DRAG_DROP
domains: [Ports and Protocols]
difficulty: MEDIUM
explanation: |
  IANA well-known ports.
---

# Question

Match each protocol to its default port.

## Draggables

- HTTP
- HTTPS
- SSH

## Dropzones

- 80
- 443
- 22

## Pairs

- HTTP -> 80
> Unencrypted web traffic uses port 80.
- HTTPS -> 443
- SSH -> 22
"""

VALID_SIMULATION = """---
type: SIMULATION
domains: [System Hardening]
difficulty: HARD
explanation: |
  Order matters.
---

# Task

Harden the SSH server in the correct order.

## Steps

1. Back up the config
> Snapshot before touching a live service.
2. Disable password authentication
3. Restart the daemon

## Distractors

- Open Telnet on port 23
> Telnet is plaintext; this undoes the hardening.
- Delete all user accounts
"""


class TestDragDrop:
    def test_parses_successfully(self):
        result = validate_dsl(VALID_DRAG_DROP)
        assert result.success is True
        assert result.errors == []
        data = result.data
        assert data["type"] == "DRAG_DROP"
        assert data["choices"] == []
        assert data["domains"] == ["Ports and Protocols"]

    def test_draggables_and_dropzones_get_ids(self):
        qd = validate_dsl(VALID_DRAG_DROP).data["question_data"]
        assert [d["id"] for d in qd["draggables"]] == ["d1", "d2", "d3"]
        assert [d["text"] for d in qd["draggables"]] == ["HTTP", "HTTPS", "SSH"]
        assert [z["id"] for z in qd["dropzones"]] == ["z1", "z2", "z3"]
        assert [z["text"] for z in qd["dropzones"]] == ["80", "443", "22"]

    def test_pairs_map_and_carry_rationale(self):
        qd = validate_dsl(VALID_DRAG_DROP).data["question_data"]
        pairs = qd["pairs"]
        assert len(pairs) == 3
        assert pairs[0] == {
            "draggable": "HTTP",
            "dropzone": "80",
            "rationale": "Unencrypted web traffic uses port 80.",
        }
        assert pairs[2]["rationale"] is None  # rationale is optional per pair

    def test_unicode_arrow_is_accepted(self):
        dsl = VALID_DRAG_DROP.replace("HTTP -> 80", "HTTP → 80")
        result = validate_dsl(dsl)
        assert result.success is True
        assert result.data["question_data"]["pairs"][0]["draggable"] == "HTTP"

    def test_unknown_draggable_is_an_error(self):
        dsl = VALID_DRAG_DROP.replace("- SSH -> 22", "- FTP -> 22")
        result = validate_dsl(dsl)
        assert result.success is False
        assert any(
            "unknown draggable 'FTP'" in e.message for e in result.errors
        )

    def test_unknown_dropzone_is_an_error(self):
        dsl = VALID_DRAG_DROP.replace("- SSH -> 22", "- SSH -> 9999")
        result = validate_dsl(dsl)
        assert result.success is False
        assert any(
            "unknown dropzone '9999'" in e.message for e in result.errors
        )

    def test_pair_without_arrow_is_an_error(self):
        dsl = VALID_DRAG_DROP.replace("- SSH -> 22", "- SSH is 22")
        result = validate_dsl(dsl)
        assert result.success is False
        assert any("draggable -> dropzone" in e.message for e in result.errors)

    def test_missing_dropzones_section_is_an_error(self):
        dsl = """---
type: DRAG_DROP
domains: [D]
---

# Question

Missing the Dropzones section.

## Draggables

- A

## Pairs

- A -> B
"""
        result = validate_dsl(dsl)
        assert result.success is False
        assert any("Missing '## Dropzones'" in e.message for e in result.errors)


class TestSimulation:
    def test_parses_successfully(self):
        result = validate_dsl(VALID_SIMULATION)
        assert result.success is True
        assert result.errors == []
        data = result.data
        assert data["type"] == "SIMULATION"
        assert data["choices"] == []
        assert "SSH server" in data["question_text"]  # the # Task text

    def test_steps_are_ordered_by_appearance(self):
        qd = validate_dsl(VALID_SIMULATION).data["question_data"]
        assert qd["total_steps"] == 3
        assert [s["order"] for s in qd["steps"]] == [1, 2, 3]
        assert qd["steps"][0]["text"] == "Back up the config"
        assert qd["steps"][0]["rationale"] == "Snapshot before touching a live service."
        assert qd["steps"][1]["rationale"] is None

    def test_ordering_ignores_the_literal_numbers(self):
        # All items numbered "1." should still come out 1, 2, 3 by appearance.
        dsl = VALID_SIMULATION.replace("2. Disable", "1. Disable").replace(
            "3. Restart", "1. Restart"
        )
        qd = validate_dsl(dsl).data["question_data"]
        assert [s["order"] for s in qd["steps"]] == [1, 2, 3]

    def test_distractors_are_optional_and_carry_rationale(self):
        qd = validate_dsl(VALID_SIMULATION).data["question_data"]
        assert len(qd["distractors"]) == 2
        assert qd["distractors"][0]["text"] == "Open Telnet on port 23"
        assert "plaintext" in qd["distractors"][0]["rationale"]
        assert qd["distractors"][1]["rationale"] is None

    def test_no_distractors_section_is_fine(self):
        dsl = VALID_SIMULATION.split("## Distractors")[0]
        result = validate_dsl(dsl)
        assert result.success is True
        assert result.data["question_data"]["distractors"] == []

    def test_missing_steps_is_an_error(self):
        dsl = """---
type: SIMULATION
domains: [D]
---

# Task

No steps here.
"""
        result = validate_dsl(dsl)
        assert result.success is False
        assert any("Missing '## Steps'" in e.message for e in result.errors)

    def test_empty_steps_section_is_an_error(self):
        dsl = """---
type: SIMULATION
domains: [D]
---

# Task

Steps header but nothing under it.

## Steps

## Distractors

- something
"""
        result = validate_dsl(dsl)
        assert result.success is False
        assert any("no steps" in e.message for e in result.errors)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
