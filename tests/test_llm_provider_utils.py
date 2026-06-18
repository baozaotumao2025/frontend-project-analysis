from frontend_project_analysis.core.config import Settings
from frontend_project_analysis.llm.provider_utils import (
    anthropic_api_path,
    gemini_api_path,
    normalize_endpoint,
    openai_api_path,
    require_provider_credentials,
)


def test_normalize_endpoint_preserves_single_separator() -> None:
    assert normalize_endpoint("https://example.com/", "v1/chat") == "https://example.com/v1/chat"


def test_provider_api_path_helpers_use_expected_defaults() -> None:
    settings = Settings.model_construct(llm_api_path="", llm_model="model")
    assert openai_api_path(settings) == "/"
    assert anthropic_api_path(settings) == "/v1/messages"
    assert gemini_api_path(settings) == "/models/model:generateContent"


def test_require_provider_credentials_rejects_missing_values() -> None:
    settings = Settings.model_construct(llm_model="", llm_api_key="")

    try:
        require_provider_credentials(settings)
    except Exception as exc:
        assert "FPA_LLM_MODEL" in str(exc)
