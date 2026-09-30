from pathlib import Path

from fastapi import APIRouter
from fastapi import Depends
from fastapi import Form
from fastapi import HTTPException
from fastapi import Request

from fastapi.responses import HTMLResponse
from fastapi.responses import RedirectResponse

from fastapi.templating import Jinja2Templates

from sqlalchemy import select
from sqlalchemy.orm import Session
from sqlalchemy.orm import selectinload

from .config import get_settings
from .database import get_db
from .models import Plan
from .models import User

from .schemas import FeedbackRequest
from .schemas import FeedbackResponse
from .schemas import UserInput
from .schemas import WorkoutResponse

from .services.gemini_client import GeminiServiceError
from .services.gemini_flash_generator import (
    generate_nutrition_tip_with_flash
)
from .services.gemini_generator import (
    generate_workout_gemini
)
from .services.updated_plan import (
    update_workout_plan
)


BASE_DIR = Path(__file__).resolve().parent.parent


templates = Jinja2Templates(
    directory=str(
        BASE_DIR / "templates"
    )
)


router = APIRouter()


def get_user(
    db: Session,
    user_id: str
):

    return db.scalar(
        select(User)
        .where(
            User.user_id == user_id
        )
        .options(
            selectinload(User.plans)
        )
    )


def save_or_update_user(
    db: Session,
    data: UserInput
):

    user = get_user(
        db,
        data.user_id
    )

    if user is None:

        user = User(
            user_id=data.user_id,
            name=data.name,
            age=data.age,
            weight_kg=data.weight_kg,
            goal=data.goal,
            intensity=data.intensity
        )

        db.add(user)

    else:

        user.name = data.name
        user.age = data.age
        user.weight_kg = data.weight_kg
        user.goal = data.goal
        user.intensity = data.intensity

    db.commit()

    db.refresh(user)

    return user


def latest_plan(
    user: User
):

    if not user.plans:

        return None

    return sorted(
        user.plans,
        key=lambda plan: plan.id,
        reverse=True
    )[0]


@router.get(
    "/",
    response_class=HTMLResponse
)
def home(
    request: Request
):

    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "title": "FitBuddy"
        }
    )


@router.post(
    "/generate-workout",
    response_class=HTMLResponse
)
def generate_workout_form(
    request: Request,

    user_id: str = Form(...),

    name: str = Form(...),

    age: int = Form(...),

    weight_kg: float = Form(...),

    goal: str = Form(...),

    intensity: str = Form(...),

    db: Session = Depends(get_db)
):

    try:

        data = UserInput(
            user_id=user_id,
            name=name,
            age=age,
            weight_kg=weight_kg,
            goal=goal,
            intensity=intensity
        )

        workout_plan = generate_workout_gemini(
            data
        )

        nutrition_tip = (
            generate_nutrition_tip_with_flash(
                data
            )
        )

        user = save_or_update_user(
            db,
            data
        )

        plan = Plan(
            user_id=user.id,
            original_plan=workout_plan,
            nutrition_tip=nutrition_tip
        )

        db.add(plan)

        db.commit()

        return templates.TemplateResponse(
            request=request,
            name="result.html",
            context={
                "title": "Your FitBuddy Plan",

                "user": user,

                "plan": plan,

                "display_plan":
                    plan.original_plan,

                "message":
                    "Your personalized plan has been generated.",

                "error": None
            }
        )

    except (
        ValueError,
        GeminiServiceError
    ) as exc:

        return templates.TemplateResponse(
            request=request,
            name="index.html",
            status_code=400,
            context={
                "title": "FitBuddy",
                "error": str(exc)
            }
        )


@router.post(
    "/submit-feedback",
    response_class=HTMLResponse
)
def submit_feedback_form(
    request: Request,

    user_id: str = Form(...),

    feedback: str = Form(...),

    db: Session = Depends(get_db)
):

    settings = get_settings()

    try:

        request_data = FeedbackRequest(
            user_id=user_id,
            feedback=feedback
        )

        if len(
            request_data.feedback
        ) > settings.max_plan_feedback_length:

            raise ValueError(
                "Feedback is too long."
            )

        user = get_user(
            db,
            request_data.user_id
        )

        if not user:

            raise ValueError(
                "User ID was not found."
            )

        plan = latest_plan(user)

        if not plan:

            raise ValueError(
                "No workout plan exists for this user."
            )

        updated = update_workout_plan(
            original_plan=(
                plan.updated_plan
                or
                plan.original_plan
            ),

            feedback=request_data.feedback,

            age=user.age,

            goal=user.goal,

            intensity=user.intensity
        )

        plan.updated_plan = updated

        plan.feedback = (
            request_data.feedback
        )

        db.commit()

        return templates.TemplateResponse(
            request=request,
            name="result.html",
            context={
                "title":
                    "Updated FitBuddy Plan",

                "user": user,

                "plan": plan,

                "display_plan":
                    plan.updated_plan,

                "message":
                    "Your plan was updated from your feedback.",

                "error": None
            }
        )

    except (
        ValueError,
        GeminiServiceError
    ) as exc:

        return templates.TemplateResponse(
            request=request,
            name="feedback.html",
            status_code=400,
            context={
                "title": "Feedback",

                "error": str(exc),

                "user_id": user_id
            }
        )


@router.get(
    "/feedback/{user_id}",
    response_class=HTMLResponse
)
def feedback_page(
    request: Request,
    user_id: str
):

    return templates.TemplateResponse(
        request=request,
        name="feedback.html",
        context={
            "title": "Update Plan",

            "user_id": user_id,

            "error": None
        }
    )


@router.post(
    "/api/workout",
    response_model=WorkoutResponse
)
def generate_workout_api(
    data: UserInput,

    db: Session = Depends(get_db)
):

    try:

        workout_plan = (
            generate_workout_gemini(
                data
            )
        )

        nutrition_tip = (
            generate_nutrition_tip_with_flash(
                data
            )
        )

        user = save_or_update_user(
            db,
            data
        )

        plan = Plan(
            user_id=user.id,
            original_plan=workout_plan,
            nutrition_tip=nutrition_tip
        )

        db.add(plan)

        db.commit()

        return WorkoutResponse(
            user_id=data.user_id,
            name=data.name,
            goal=data.goal,
            intensity=data.intensity,
            workout_plan=workout_plan,
            nutrition_tip=nutrition_tip
        )

    except GeminiServiceError as exc:

        raise HTTPException(
            status_code=502,
            detail=str(exc)
        ) from exc


@router.post(
    "/api/feedback",
    response_model=FeedbackResponse
)
def feedback_api(
    data: FeedbackRequest,

    db: Session = Depends(get_db)
):

    user = get_user(
        db,
        data.user_id
    )

    if not user:

        raise HTTPException(
            status_code=404,
            detail="User ID was not found."
        )

    plan = latest_plan(user)

    if not plan:

        raise HTTPException(
            status_code=404,
            detail="No workout plan exists."
        )

    try:

        updated = update_workout_plan(
            original_plan=(
                plan.updated_plan
                or
                plan.original_plan
            ),

            feedback=data.feedback,

            age=user.age,

            goal=user.goal,

            intensity=user.intensity
        )

        plan.updated_plan = updated

        plan.feedback = data.feedback

        db.commit()

        return FeedbackResponse(
            user_id=user.user_id,
            updated_plan=updated,
            nutrition_tip=plan.nutrition_tip
        )

    except GeminiServiceError as exc:

        raise HTTPException(
            status_code=502,
            detail=str(exc)
        ) from exc


def require_admin(
    request: Request
):

    settings = get_settings()

    supplied = (
        request.headers.get(
            "X-Admin-Password"
        )
        or
        request.query_params.get(
            "admin_password"
        )
    )

    if (
        not supplied
        or
        supplied != settings.admin_password
    ):

        raise HTTPException(
            status_code=401,
            detail="Invalid admin password."
        )


@router.get(
    "/admin/login",
    response_class=HTMLResponse
)
def admin_login(
    request: Request
):

    return templates.TemplateResponse(
        request=request,
        name="admin_login.html",
        context={
            "title": "Admin Login",
            "error": None
        }
    )


@router.post(
    "/admin/login",
    response_class=HTMLResponse
)
def admin_login_submit(
    request: Request,

    password: str = Form(...)
):

    settings = get_settings()

    if password != settings.admin_password:

        return templates.TemplateResponse(
            request=request,
            name="admin_login.html",
            status_code=401,
            context={
                "title": "Admin Login",

                "error":
                    "Invalid password."
            }
        )

    return RedirectResponse(
        url=(
            "/view-all-users"
            f"?admin_password={password}"
        ),
        status_code=303
    )


@router.get(
    "/view-all-users",
    response_class=HTMLResponse
)
def view_all_users(
    request: Request,

    db: Session = Depends(get_db)
):

    require_admin(request)

    users = db.scalars(
        select(User)
        .options(
            selectinload(User.plans)
        )
        .order_by(
            User.id.desc()
        )
    ).all()

    return templates.TemplateResponse(
        request=request,
        name="all_users.html",
        context={
            "title": "All Users",

            "users": users,

            "admin_password":
                request.query_params.get(
                    "admin_password"
                )
        }
    )


@router.get(
    "/api/users"
)
def list_users(
    request: Request,

    db: Session = Depends(get_db)
):

    require_admin(request)

    users = db.scalars(
        select(User)
        .options(
            selectinload(User.plans)
        )
    ).all()

    return [
        {
            "user_id": user.user_id,

            "name": user.name,

            "age": user.age,

            "weight_kg": user.weight_kg,

            "goal": user.goal,

            "intensity": user.intensity,

            "plans": [
                {
                    "id": plan.id,

                    "original_plan":
                        plan.original_plan,

                    "updated_plan":
                        plan.updated_plan,

                    "feedback":
                        plan.feedback,

                    "nutrition_tip":
                        plan.nutrition_tip
                }

                for plan in user.plans
            ]
        }

        for user in users
    ]


@router.delete(
    "/api/users/{user_id}"
)
def delete_user(
    user_id: str,

    request: Request,

    db: Session = Depends(get_db)
):

    require_admin(request)

    user = db.scalar(
        select(User)
        .where(
            User.user_id == user_id
        )
    )

    if not user:

        raise HTTPException(
            status_code=404,
            detail="User ID was not found."
        )

    db.delete(user)

    db.commit()

    return {
        "message": "User deleted.",
        "user_id": user_id
    }


@router.get("/health")
def health():

    return {
        "status": "ok",
        "service": "FitBuddy"
    }