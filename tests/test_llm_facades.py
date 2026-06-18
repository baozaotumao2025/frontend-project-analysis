from frontend_project_analysis.llm import run_semantic_review
from frontend_project_analysis.llm.transport.errors import (
    error_code_for_http_message,
    error_for_http_failure,
)
from frontend_project_analysis.llm.transport.retry import (
    should_retry_http,
    sleep_backoff,
)


def test_llm_facade_exposes_router() -> None:
    assert run_semantic_review.__name__ == "run_semantic_review"


def test_llm_package_exposes_transport_helpers() -> None:
    assert error_code_for_http_message("HTTP 429") is not None
    assert callable(error_for_http_failure)
    assert callable(should_retry_http)
    assert callable(sleep_backoff)
