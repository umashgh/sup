"""
Question resolver for dynamic questioning logic.
Filters questions based on scenario, tier, and conditional logic.
"""

import copy
from typing import List, Dict, Optional
from .questions import ALL_QUESTIONS, Question


def get_questions_for_scenario(
    scenario_type: str,
    tier: str,
    user_data: Optional[Dict] = None,
    skip_conditions: bool = False,
) -> List[Question]:
    """
    Returns filtered list of questions based on scenario, tier, and conditional logic.

    Args:
        scenario_type: The user's selected scenario (FOUNDER, RETIREMENT, etc.)
        tier: The current tier (QUICK, STANDARD, ADVANCED)
        user_data: User's current answers (used for conditional logic)
        skip_conditions: If True, include all questions regardless of conditions.
            Set True when client handles conditional visibility (e.g. Alpine.js).

    Returns:
        List of Question objects that should be shown to the user
    """
    user_data = user_data or {}

    filtered_questions = []

    for question in ALL_QUESTIONS:
        # Check if question applies to this scenario
        if scenario_type not in question.scenarios:
            continue

        # Check if question is for this tier
        if question.tier != tier:
            continue

        # Check conditional logic (if present) — skip if client handles it
        if not skip_conditions and question.condition is not None:
            try:
                if not question.condition(user_data):
                    continue
            except Exception as e:
                # If condition evaluation fails, skip the question
                print(f"Warning: Condition evaluation failed for question {question.id}: {e}")
                continue

        # Apply scenario-specific label/help overrides (shallow copy to avoid mutating global list)
        if question.text_by_scenario.get(scenario_type) or question.help_by_scenario.get(scenario_type):
            q = copy.copy(question)
            if scenario_type in q.text_by_scenario:
                q.text = q.text_by_scenario[scenario_type]
            if scenario_type in q.help_by_scenario:
                q.help_text = q.help_by_scenario[scenario_type]
            filtered_questions.append(q)
        else:
            filtered_questions.append(question)

    return filtered_questions


def validate_answer(question: Question, answer: any) -> tuple[bool, Optional[str]]:
    """
    Validates a user's answer against question validation rules.

    Args:
        question: The Question object
        answer: The user's answer

    Returns:
        Tuple of (is_valid, error_message)
    """
    if not question.validation:
        return True, None

    # Check required
    if question.validation.get('required', False) and not answer:
        return False, "This field is required"

    # Check min/max for numeric values
    if isinstance(answer, (int, float)):
        min_val = question.validation.get('min')
        max_val = question.validation.get('max')

        if min_val is not None and answer < min_val:
            return False, f"Value must be at least {min_val}"

        if max_val is not None and answer > max_val:
            return False, f"Value must be at most {max_val}"

    return True, None


def get_required_fields_for_tier(scenario_type: str, tier: str) -> List[str]:
    """
    Returns list of required field names for a given scenario and tier.

    Args:
        scenario_type: The user's selected scenario
        tier: The current tier

    Returns:
        List of field names that are required for this tier
    """
    questions = get_questions_for_scenario(scenario_type, tier)

    required_fields = []
    for question in questions:
        if question.validation.get('required', False):
            required_fields.append(question.field_name)

    return required_fields
