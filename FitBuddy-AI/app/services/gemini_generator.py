from ..config import get_settings
from ..schemas import UserInput

from .gemini_client import generate_text


SYSTEM_RULES = """
You are FitBuddy, an educational wellness planning assistant.

Create practical and conservative exercise guidance.

Do not diagnose diseases.

Do not prescribe medication or supplements.

Do not provide calorie targets, starvation advice,
extreme weight-loss instructions, dangerous challenges,
or instructions that encourage exercising through pain.

For users under 18, avoid weight-loss or body-composition goals.
Emphasize general fitness, enjoyment, strength, mobility,
sleep and recovery.

Always include a short reminder to stop if pain, dizziness,
breathing difficulty, or another concerning symptom occurs
and seek appropriate help.
"""


def generate_workout_gemini(
    user: UserInput
) -> str:

    settings = get_settings()

    goal = user.goal

    if user.age < 18 and goal == "weight loss":

        goal = "general wellness"

    prompt = f"""
{SYSTEM_RULES}

Create a personalized 7-day beginner-to-intermediate
wellness plan.

User information:

Name: {user.name}

Age: {user.age}

Weight: {user.weight_kg} kg

Requested goal: {user.goal}

Planning goal: {goal}

Workout intensity: {user.intensity}

Format the answer as readable Markdown/text.

Use:

Title

Safety note

Day 1
Day 2
Day 3
Day 4
Day 5
Day 6
Day 7

For every day include:

- Focus
- Warm-up
- Main activity
- Exercise names
- Sets/repetitions OR time
- Rest/recovery
- Cool-down

Also include:

Weekly progression note.

Keep the plan realistic.

Include rest/recovery days.

Do not provide medical treatment.
"""

    return generate_text(
        prompt,
        model=settings.gemini_workout_model,
        max_output_tokens=3500
    )