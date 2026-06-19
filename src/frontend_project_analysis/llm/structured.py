"""Shared helpers for structured LLM requests."""

from __future__ import annotations

from ..core.config import Settings
from ..schemas import AnthropicReviewRequest, GeminiReviewRequest, OpenAIReviewRequest


def build_openai_structured_request(
    *,
    settings: Settings,
    system_prompt: str,
    user_prompt: str,
    schema_name: str,
    schema: dict,
    strict: bool = True,
) -> dict:
    return OpenAIReviewRequest(
        model=settings.llm_model or "",
        input=[
            {"role": "developer", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        text={
            "format": {
                "type": "json_schema",
                "name": schema_name,
                "schema": schema,
                "strict": strict,
            }
        },
        max_output_tokens=settings.llm_max_output_tokens,
    ).model_dump()


def build_anthropic_structured_request(
    *,
    settings: Settings,
    system_prompt: str,
    user_prompt: str,
) -> dict:
    return AnthropicReviewRequest(
        model=settings.llm_model or "",
        max_tokens=settings.llm_max_output_tokens,
        system=system_prompt,
        messages=[{"role": "user", "content": user_prompt}],
    ).model_dump()


def build_gemini_structured_request(
    *,
    settings: Settings,
    system_prompt: str,
    user_prompt: str,
) -> dict:
    return GeminiReviewRequest(
        system_instruction={"parts": [{"text": system_prompt}]},
        contents=[{"role": "user", "parts": [{"text": user_prompt}]}],
        generationConfig={
            "temperature": settings.llm_temperature,
            "maxOutputTokens": settings.llm_max_output_tokens,
            "responseMimeType": "application/json",
        },
    ).model_dump()
