import os

os.environ["DATABASE_URL"] = (
    "sqlite:///./test_fitbuddy.db"
)

os.environ["ADMIN_PASSWORD"] = "test-admin"


from fastapi.testclient import TestClient

from app.main import app

from app import routes


client = TestClient(app)


def fake_workout(data):

    return """
Day 1: Full body

Day 2: Recovery

Day 3: Mobility

Day 4: Full body

Day 5: Cardio

Day 6: Strength

Day 7: Rest
"""


def fake_tip(data):

    return (
        "Prioritize regular balanced meals, "
        "hydration and recovery."
    )


def fake_update(
    original_plan,
    feedback,
    age,
    goal,
    intensity
):

    return (
        original_plan
        +
        "\nUpdated from feedback: "
        +
        feedback
    )


def test_home():

    response = client.get("/")

    assert response.status_code == 200

    assert "FitBuddy" in response.text


def test_health():

    response = client.get("/health")

    assert response.status_code == 200

    assert (
        response.json()["status"]
        == "ok"
    )


def test_api_workout(
    monkeypatch
):

    monkeypatch.setattr(
        routes,
        "generate_workout_gemini",
        fake_workout
    )

    monkeypatch.setattr(
        routes,
        "generate_nutrition_tip_with_flash",
        fake_tip
    )


    response = client.post(
        "/api/workout",

        json={
            "user_id": "TEST001",

            "name": "Test User",

            "age": 25,

            "weight_kg": 65,

            "goal":
                "general wellness",

            "intensity":
                "medium"
        }
    )


    assert response.status_code == 200

    assert (
        "Day 1"
        in
        response.json()["workout_plan"]
    )


def test_api_feedback(
    monkeypatch
):

    monkeypatch.setattr(
        routes,
        "update_workout_plan",
        fake_update
    )


    response = client.post(
        "/api/feedback",

        json={
            "user_id": "TEST001",

            "feedback":
                "Add more mobility."
        }
    )


    assert response.status_code == 200

    assert (
        "Add more mobility"
        in
        response.json()["updated_plan"]
    )


def test_admin_requires_password():

    response = client.get(
        "/api/users"
    )

    assert response.status_code == 401