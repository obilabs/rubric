"""
Question DSL Parser - Parse Rubric DSL into structured question data.

Supports all question types with validation and error reporting.
"""

from typing import Dict, Any, List, Optional
import yaml
import re
import json
from dataclasses import dataclass, field


@dataclass
class ParseError:
    """Represents a parse error with location information."""
    line: int
    message: str
    severity: str = "error"  # error, warning


@dataclass
class ParseResult:
    """Result of parsing DSL."""
    success: bool
    data: Optional[Dict[str, Any]] = None
    errors: List[ParseError] = field(default_factory=list)
    warnings: List[ParseError] = field(default_factory=list)


class QuestionDSLParser:
    """Parse Rubric DSL into structured question data."""

    VALID_TYPES = [
        'SINGLE_CHOICE',  # New name for consistency
        'MULTIPLE_CHOICE',  # Deprecated alias for SINGLE_CHOICE
        'MULTIPLE_SELECT',
        'TRUE_FALSE',
        'HOTSPOT',
        'DRAG_DROP',
        'CASE_STUDY',
        'SIMULATION'
    ]

    VALID_DIFFICULTIES = ['EASY', 'MEDIUM', 'HARD']

    def parse(self, dsl: str) -> ParseResult:
        """
        Parse DSL string into question dict.

        Args:
            dsl: Question in DSL format

        Returns:
            ParseResult with data or errors
        """
        errors = []
        warnings = []

        try:
            # Split frontmatter and content
            parts = re.split(r'^---\s*$', dsl, flags=re.MULTILINE)

            if len(parts) < 3:
                errors.append(ParseError(
                    line=1,
                    message="Invalid DSL format: missing frontmatter delimiters (---)"
                ))
                return ParseResult(success=False, errors=errors)

            # Parse frontmatter (YAML)
            try:
                frontmatter = yaml.safe_load(parts[1])
                if not isinstance(frontmatter, dict):
                    errors.append(ParseError(
                        line=2,
                        message="Frontmatter must be valid YAML dictionary"
                    ))
                    return ParseResult(success=False, errors=errors)
            except yaml.YAMLError as e:
                errors.append(ParseError(
                    line=2,
                    message=f"Invalid YAML in frontmatter: {str(e)}"
                ))
                return ParseResult(success=False, errors=errors)

            # Validate required fields
            if 'type' not in frontmatter:
                errors.append(ParseError(
                    line=2,
                    message="Missing required field: 'type'"
                ))
                return ParseResult(success=False, errors=errors)

            qtype = frontmatter['type']
            if qtype not in self.VALID_TYPES:
                errors.append(ParseError(
                    line=2,
                    message=f"Invalid type '{qtype}'. Must be one of: {', '.join(self.VALID_TYPES)}"
                ))
                return ParseResult(success=False, errors=errors)

            # Validate difficulty. An invalid value is reported as a warning and
            # then normalized to MEDIUM, so data['difficulty'] never carries a
            # value outside VALID_DIFFICULTIES (this is what FORMAT.md documents).
            if 'difficulty' in frontmatter:
                difficulty = frontmatter['difficulty']
                if difficulty not in self.VALID_DIFFICULTIES:
                    warnings.append(ParseError(
                        line=2,
                        message=f"Invalid difficulty '{difficulty}'. Defaulting to MEDIUM",
                        severity="warning"
                    ))
                    frontmatter['difficulty'] = 'MEDIUM'

            # Parse content based on type
            content = parts[2]

            if qtype in ['SINGLE_CHOICE', 'MULTIPLE_CHOICE', 'MULTIPLE_SELECT', 'TRUE_FALSE']:
                result = self._parse_choice_question(content, frontmatter, errors, warnings)
            elif qtype == 'HOTSPOT':
                result = self._parse_hotspot_question(content, frontmatter, errors, warnings)
            elif qtype == 'DRAG_DROP':
                result = self._parse_drag_drop_question(content, frontmatter, errors, warnings)
            elif qtype == 'CASE_STUDY':
                result = self._parse_case_study_question(content, frontmatter, errors, warnings)
            elif qtype == 'SIMULATION':
                result = self._parse_simulation_question(content, frontmatter, errors, warnings)
            else:
                errors.append(ParseError(
                    line=1,
                    message=f"Parser not implemented for type: {qtype}"
                ))
                return ParseResult(success=False, errors=errors)

            if errors:
                return ParseResult(success=False, data=result, errors=errors, warnings=warnings)

            return ParseResult(success=True, data=result, warnings=warnings)

        except Exception as e:
            errors.append(ParseError(
                line=0,
                message=f"Unexpected parsing error: {str(e)}"
            ))
            return ParseResult(success=False, errors=errors)

    def _parse_choice_question(
        self,
        content: str,
        frontmatter: Dict[str, Any],
        errors: List[ParseError],
        warnings: List[ParseError]
    ) -> Dict[str, Any]:
        """Parse MULTIPLE_CHOICE or MULTIPLE_SELECT question."""

        # Extract question text
        question_match = re.search(
            r'#\s+Question\s*\n(.*?)(?=##|\Z)',
            content,
            re.DOTALL
        )

        if not question_match:
            errors.append(ParseError(
                line=self._find_line(content, "# Question"),
                message="Missing '# Question' section"
            ))
            question_text = ""
        else:
            question_text = question_match.group(1).strip()

        # Parse image references in question text
        question_text = self._parse_images(question_text)

        # Extract choices
        choices_match = re.search(
            r'##\s+Choices\s*\n(.*?)(?=##|---|\Z)',
            content,
            re.DOTALL
        )

        choices = []
        if not choices_match:
            errors.append(ParseError(
                line=self._find_line(content, "## Choices"),
                message="Missing '## Choices' section"
            ))
        else:
            choices_text = choices_match.group(1)
            choices = self._parse_choices(choices_text, errors, warnings)

        # Validate correct answer count
        correct_count = sum(1 for c in choices if c.get('is_correct', False))
        qtype = frontmatter['type']

        if qtype in ['SINGLE_CHOICE', 'MULTIPLE_CHOICE'] and correct_count != 1:
            errors.append(ParseError(
                line=self._find_line(content, "## Choices"),
                message=f"{qtype} must have exactly 1 correct answer, found {correct_count}"
            ))
        elif qtype == 'MULTIPLE_SELECT' and correct_count < 2:
            errors.append(ParseError(
                line=self._find_line(content, "## Choices"),
                message=f"MULTIPLE_SELECT must have at least 2 correct answers, found {correct_count}"
            ))
        elif qtype == 'TRUE_FALSE':
            if len(choices) != 2:
                errors.append(ParseError(
                    line=self._find_line(content, "## Choices"),
                    message=f"TRUE_FALSE must have exactly 2 choices, found {len(choices)}"
                ))
            elif correct_count != 1:
                errors.append(ParseError(
                    line=self._find_line(content, "## Choices"),
                    message=f"TRUE_FALSE must have exactly 1 correct answer, found {correct_count}"
                ))

        # Build result
        result = {
            "type": qtype,
            "domains": frontmatter.get('domains', []),
            "difficulty": frontmatter.get('difficulty', 'MEDIUM'),
            "tags": frontmatter.get('tags', []),
            "question_text": question_text,
            "choices": choices,
            "explanation": frontmatter.get('explanation', ''),
            "question_data": {}
        }

        # Add correct_count for MULTIPLE_SELECT questions
        if qtype == 'MULTIPLE_SELECT':
            result["correct_count"] = correct_count

        return result

    def _parse_choices(
        self,
        choices_text: str,
        errors: List[ParseError],
        warnings: List[ParseError]
    ) -> List[Dict[str, Any]]:
        """Parse choices from text.

        A choice may be followed by one or more '>' lines giving the rationale
        for that specific option — why it is right, or which misconception it
        represents. Optional and per-choice; questions without them are
        unaffected. Distractors encode misconceptions, so explaining the option
        the learner actually picked addresses their real error rather than
        restating the correct answer.

            A. 3,000 *[CORRECT]*
            > 15 x 200 = 3000.
            B. 2,500
            > Subtracts instead of multiplying.
        """
        choices = []
        choice_pattern = r'^([A-Z])\.\s*(.*?)(?:\*\[CORRECT\]\*)?$'

        for line_num, line in enumerate(choices_text.split('\n'), 1):
            line = line.strip()
            if not line:
                continue

            if line.startswith('>'):
                rationale = line.lstrip('>').strip()
                if not choices:
                    warnings.append(ParseError(
                        line=line_num,
                        message="Rationale line '>' appears before any choice",
                        severity="warning"
                    ))
                elif rationale:
                    previous = choices[-1].get("rationale")
                    choices[-1]["rationale"] = (
                        f"{previous} {rationale}" if previous else rationale
                    )
                continue

            match = re.match(choice_pattern, line)
            if match:
                letter = match.group(1)
                text = match.group(2).strip()
                is_correct = '*[CORRECT]*' in line

                # Parse images in choice text
                text = self._parse_images(text)

                choices.append({
                    "letter": letter,
                    "text": text,
                    "is_correct": is_correct,
                    "rationale": None,
                })
            else:
                warnings.append(ParseError(
                    line=line_num,
                    message=f"Could not parse choice: '{line[:50]}...'",
                    severity="warning"
                ))

        return choices

    def _parse_hotspot_question(
        self,
        content: str,
        frontmatter: Dict[str, Any],
        errors: List[ParseError],
        warnings: List[ParseError]
    ) -> Dict[str, Any]:
        """Parse HOTSPOT question."""

        # Extract question text
        question_match = re.search(
            r'#\s+Question\s*\n(.*?)(?=##|\Z)',
            content,
            re.DOTALL
        )
        question_text = question_match.group(1).strip() if question_match else ""
        question_text = self._parse_images(question_text)

        # Extract hotspot data (JSON block)
        json_match = re.search(
            r'```json\s*(.*?)```',
            content,
            re.DOTALL
        )

        hotspot_data = {}
        if json_match:
            try:
                hotspot_data = json.loads(json_match.group(1))
            except json.JSONDecodeError as e:
                errors.append(ParseError(
                    line=self._find_line(content, "```json"),
                    message=f"Invalid JSON in hotspot data: {str(e)}"
                ))
        else:
            errors.append(ParseError(
                line=self._find_line(content, "## Hotspots"),
                message="Missing hotspot data (```json block)"
            ))

        return {
            "type": "HOTSPOT",
            "domains": frontmatter.get('domains', []),
            "difficulty": frontmatter.get('difficulty', 'MEDIUM'),
            "tags": frontmatter.get('tags', []),
            "question_text": question_text,
            "choices": [],
            "explanation": frontmatter.get('explanation', ''),
            "question_data": hotspot_data
        }

    def _parse_drag_drop_question(
        self,
        content: str,
        frontmatter: Dict[str, Any],
        errors: List[ParseError],
        warnings: List[ParseError]
    ) -> Dict[str, Any]:
        """Parse DRAG_DROP question."""

        # TODO: Implement drag-drop parser
        warnings.append(ParseError(
            line=1,
            message="DRAG_DROP parser not yet implemented",
            severity="warning"
        ))

        return {
            "type": "DRAG_DROP",
            "domains": frontmatter.get('domains', []),
            "difficulty": frontmatter.get('difficulty', 'MEDIUM'),
            "tags": frontmatter.get('tags', []),
            "question_text": "",
            "choices": [],
            "explanation": frontmatter.get('explanation', ''),
            "question_data": {}
        }

    def _parse_case_study_question(
        self,
        content: str,
        frontmatter: Dict[str, Any],
        errors: List[ParseError],
        warnings: List[ParseError]
    ) -> Dict[str, Any]:
        """Parse CASE_STUDY question with nested sub-questions."""

        # Extract scenario text (# Scenario section)
        scenario_match = re.search(
            r'#\s+Scenario\s*\n(.*?)(?=##|\Z)',
            content,
            re.DOTALL
        )

        if not scenario_match:
            errors.append(ParseError(
                line=self._find_line(content, "# Scenario"),
                message="Missing '# Scenario' section in case study"
            ))
            scenario_text = ""
        else:
            scenario_text = scenario_match.group(1).strip()
            scenario_text = self._parse_images(scenario_text)

        # Extract all sub-questions (## Question N sections)
        sub_question_pattern = r'##\s+Question\s+(\d+)\s*\n(.*?)(?=##\s+Question\s+\d+|\Z)'
        sub_question_matches = re.finditer(sub_question_pattern, content, re.DOTALL)

        sub_questions = []
        for match in sub_question_matches:
            question_num = int(match.group(1))
            question_content = match.group(2)

            # Parse sub-question text (before ### Choices)
            sub_q_text_match = re.search(
                r'^(.*?)(?=###|$)',
                question_content,
                re.DOTALL
            )
            sub_q_text = sub_q_text_match.group(1).strip() if sub_q_text_match else ""
            sub_q_text = self._parse_images(sub_q_text)

            # Extract choices (### Choices section)
            choices_match = re.search(
                r'###\s+Choices\s*\n(.*?)(?=###|$)',
                question_content,
                re.DOTALL
            )

            choices = []
            if not choices_match:
                errors.append(ParseError(
                    line=self._find_line(content, f"## Question {question_num}"),
                    message=f"Missing '### Choices' section in Question {question_num}"
                ))
            else:
                choices_text = choices_match.group(1)
                choices = self._parse_choices(choices_text, errors, warnings)

            # Extract explanation (### Explanation section)
            explanation_match = re.search(
                r'###\s+Explanation\s*\n(.*?)(?=###|##|$)',
                question_content,
                re.DOTALL
            )
            explanation = explanation_match.group(1).strip() if explanation_match else ""

            # Determine sub-question type (single or multiple select)
            correct_count = sum(1 for c in choices if c.get('is_correct', False))
            sub_q_type = "MULTIPLE_SELECT" if correct_count > 1 else "SINGLE_CHOICE"

            sub_question = {
                "question_number": question_num,
                "question_type": sub_q_type,
                "question_text": sub_q_text,
                "choices": choices,
                "explanation": explanation,
                "correct_count": correct_count if sub_q_type == "MULTIPLE_SELECT" else None
            }

            sub_questions.append(sub_question)

        # Validate at least one sub-question
        if len(sub_questions) == 0:
            errors.append(ParseError(
                line=self._find_line(content, "# Scenario"),
                message="Case study must have at least one sub-question"
            ))

        return {
            "type": "CASE_STUDY",
            "domains": frontmatter.get('domains', []),
            "difficulty": frontmatter.get('difficulty', 'MEDIUM'),
            "tags": frontmatter.get('tags', []),
            "question_text": scenario_text,  # Scenario becomes the parent question text
            "choices": [],  # Case study parent has no choices
            "explanation": None,  # Case study parent has no explanation
            "question_data": {
                "total_sub_questions": len(sub_questions)
            },
            "sub_questions": sub_questions
        }

    def _parse_simulation_question(
        self,
        content: str,
        frontmatter: Dict[str, Any],
        errors: List[ParseError],
        warnings: List[ParseError]
    ) -> Dict[str, Any]:
        """Parse SIMULATION question."""

        # TODO: Implement simulation parser
        warnings.append(ParseError(
            line=1,
            message="SIMULATION parser not yet implemented",
            severity="warning"
        ))

        return {
            "type": "SIMULATION",
            "domains": frontmatter.get('domains', []),
            "difficulty": frontmatter.get('difficulty', 'MEDIUM'),
            "tags": frontmatter.get('tags', []),
            "question_text": "",
            "choices": [],
            "explanation": frontmatter.get('explanation', ''),
            "question_data": {}
        }

    def _parse_images(self, text: str) -> str:
        """Parse [IMAGE: filename] references."""
        # For now, just return as-is
        # Later we can validate image existence
        return text

    def _find_line(self, content: str, search: str) -> int:
        """Find line number of search string in content."""
        lines = content.split('\n')
        for i, line in enumerate(lines, 1):
            if search in line:
                return i
        return 0


def validate_dsl(dsl: str) -> ParseResult:
    """Convenience function to validate DSL."""
    parser = QuestionDSLParser()
    return parser.parse(dsl)
