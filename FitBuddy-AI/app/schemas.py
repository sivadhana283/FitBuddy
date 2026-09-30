from typing import Literal

from pydantic import BaseModel
from pydantic import Field
from pydantic import field_validator


Goal = Literal[
    "weight loss",
    "muscle gain",
    "general wellness",
    "flexibility"
]


Intensity = Literal[
    "low",
    "medium",
    "high"
]


class UserInput(BaseModel):

    user_id: str = Field(
        min_length=2,
        max_length=80
    )

    name: str = Field(
        min_length=1,
        max_length=100
    )

    age: int = Field(
        ge=13,
        le=100
    )

    weight_kg: float = Field(
        gt=0,
        le=500
    )

    goal: Goal

    intensity: Intensity

    @field_validator("user_id", "name")
    @classmethod
    def strip_text(cls, value: str) -> str:

        value = value.strip()

        if not value:
            raise ValueError(
                "Value cannot be empty"
            )

        return value


class FeedbackRequest(BaseModel):

    user_id: str = Field(
        min_length=2,
        max_length=80
    )

    feedback: str = Field(
        min_length=3,
        max_length=1000
    )


class WorkoutResponse(BaseModel):

    user_id: str

    name: str

    goal: str

    intensity: str

    workout_plan: str

    nutrition_tip: str


class FeedbackResponse(BaseModel):

    user_id: str

    updated_plan: str

    nutrition_tip: str