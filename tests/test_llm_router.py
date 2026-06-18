from frontend_project_analysis.llm import run_semantic_review


def test_llm_router_entrypoint_remains_available() -> None:
    assert run_semantic_review.__name__ == "run_semantic_review"
