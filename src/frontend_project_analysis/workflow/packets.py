"""Semantic packet construction helpers."""

from __future__ import annotations

from ..core.domain import SEMANTIC_REVIEW_RUBRICS
from ..models import Artifact, Project
from .evidence import artifact_ref, build_semantic_evidence_snapshot


def build_semantic_packet(session, project: Project, artifact: Artifact) -> dict:
    evidence = build_semantic_evidence_snapshot(session, project, artifact)
    dependencies = [artifact_ref(dep.to_artifact) for dep in artifact.outgoing_dependencies]
    dependents = [artifact_ref(dep.from_artifact) for dep in artifact.incoming_dependencies]
    metadata = dict(artifact.metadata_json or {})
    body = ""
    if artifact.current_version:
        metadata = dict(artifact.current_version.metadata_json or metadata)
        body = artifact.current_version.body_snapshot
    return {
        "project": {"key": project.key, "name": project.name},
        "artifact": {
            "ref": artifact_ref(artifact),
            "type": artifact.artifact_type.value,
            "title": artifact.title,
            "slug": artifact.slug,
            "round": artifact.round,
            "status": artifact.status.value,
            "source_path": artifact.source_path,
        },
        "metadata": metadata,
        "body": body,
        "dependencies": dependencies,
        "dependents": dependents,
        "analysis_inventory": [
            {
                "ref": item.ref,
                "role": item.role,
                "status": item.status,
                "source_path": item.source_path,
                "source_exists": item.source_exists,
                "has_version": item.has_version,
            }
            for item in evidence.inventory
        ],
        "coverage_ledger": [
            {
                "ref": item.ref,
                "role": item.role,
                "disposition": item.disposition,
                "reason": item.reason,
            }
            for item in evidence.inventory
        ],
        "frozen_packet": True,
        "rubric": SEMANTIC_REVIEW_RUBRICS[artifact.artifact_type],
        "fresh_session_required": True,
        "packet_only": True,
    }
