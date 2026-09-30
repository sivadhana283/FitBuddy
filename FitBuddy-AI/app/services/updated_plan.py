from ..config import get_settings

from .gemini_client import generate_text


def update_workout_plan(
    original_plan: str,
    feedback: str,
    age: int,
    goal: str,
    intensity: str
) -> str:

    settings = get_settings()

    safe_goal = goal

    if age < 18 and goal == "weight loss":

        safe_goal = "general wellness"

    prompt = f"""
You are FitBuddy's plan revision assistant.

Original workout plan:

{original_plan}

User feedback:

{feedback}

User information:

Age: {age}

Goal: {safe_goal}

Intensity: {intensity}

Regenerate the FULL 7-day plan.

Do not only provide the changes.

Respect reasonable rest and recovery.

Do not:

- Diagnose diseases
- Prescribe medication
- Prescribe supplements
- Give calorie targets
- Give extreme weight-loss instructions
- Give unsafe exercise challenges
- Encourage exercising through pain

For users under 18, focus on:

- General fitness
- Enjoyment
- Strength
- Mobility
- Recovery

Use clear:

Day 1
Day 2
Day 3
Day 4
Day 5
Day 6
Day 7

headings.

Include:

- Warm-up
- Main activity
- Recovery/rest
- Cool-down
"""

    return generate_text(
        prompt,
        model=settings.gemini_workout_model,
        max_output_tokens=3500
    )