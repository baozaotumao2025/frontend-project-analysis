from frontend_project_analysis import infrastructure, models, schemas


def test_models_facade_reexports_core_entities() -> None:
    assert models.Base.__name__ == "Base"
    assert models.Project.__tablename__ == "projects"
    assert models.Artifact.__tablename__ == "artifacts"
    assert models.ArtifactReview.__tablename__ == "artifact_reviews"


def test_schemas_facade_reexports_core_payloads() -> None:
    assert schemas.SemanticReviewPayload.__name__ == "SemanticReviewPayload"
    assert schemas.ProviderAuditPayload.__name__ == "ProviderAuditPayload"
    assert schemas.OpenAIReviewRequest.__name__ == "OpenAIReviewRequest"
    assert schemas.SubmissionIntentPayload.__name__ == "SubmissionIntentPayload"


def test_infrastructure_facade_reexports_runtime_helpers() -> None:
    assert infrastructure.call_context.__name__ == "call_context"
    assert infrastructure.configure_logging.__name__ == "configure_logging"
    assert infrastructure.initialize_database.__name__ == "initialize_database"
