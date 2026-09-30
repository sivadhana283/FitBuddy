from ..config import get_settings
from ..schemas import UserInput

from .gemini_client import generate_text


def generate_nutrition_tip_with_flash(
    user: UserInput
) -> str:

    settings = get_settings()

    goal = user.goal

    if user.age < 18 and user.goal == "weight loss":

        goal = "general wellness"

    prompt = f"""
You are FitBuddy's nutrition and recovery tip assistant.

Give ONE concise and practical wellness tip.

User age:
{user.age}

Goal:
{goal}

Workout intensity:
{user.intensity}

Focus on:

- Balanced meals
- Hydration
- Regular eating
- Sleep
- Recovery

Do not give:

- Calorie targets
- Restrictive dieting
- Supplement prescriptions
- Extreme weight-loss advice

For users under 18, keep advice age-appropriate
and avoid weight-focused guidance.

Return 2–4 sentences.
"""

    return generate_text(
        prompt,
        model=settings.gemini_tip_model,
        max_output_tokens=300
    )