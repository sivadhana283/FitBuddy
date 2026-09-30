from functools import lru_cache

from google import genai

from ..config import get_settings


class GeminiServiceError(RuntimeError):
    pass


@lru_cache
def get_client():

    settings = get_settings()

    if not settings.gemini_api_key:

        raise GeminiServiceError(
            "GEMINI_API_KEY is not configured. "
            "Add it to your .env file."
        )

    return genai.Client(
        api_key=settings.gemini_api_key
    )


def generate_text(
    prompt: str,
    model: str,
    max_output_tokens: int = 3000
) -> str:

    try:

        client = get_client()

        response = client.models.generate_content(
            model=model,
            contents=prompt,
            config={
                "temperature": 0.6,
                "max_output_tokens": max_output_tokens,
            },
        )

        text = (
            response.text or ""
        ).strip()

        if not text:

            raise GeminiServiceError(
                "Gemini returned an empty response."
            )

        return text

    except GeminiServiceError:

        raise

    except Exception as exc:

        raise GeminiServiceError(
            f"Gemini request failed: {exc}"
        ) from exc