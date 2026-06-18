"""Audit archive helpers."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

from ...core.config import AppPaths


def archive_provider_call(
    paths: AppPaths,
    project_key: str,
    artifact_ref_value: str,
    audit_payload: dict,
) -> tuple[Path, Path | None]:
    timestamp = datetime.now(UTC).strftime("%Y-%m-%dT%H-%M-%S-%fZ")
    trace_id = str(audit_payload.get("trace_id", "trace"))
    request_id = str(audit_payload.get("request_id", "request"))
    artifact_dir = paths.audit_dir / project_key / artifact_ref_value.replace(":", "__")
    artifact_dir.mkdir(parents=True, exist_ok=True)
    request_path = artifact_dir / f"{timestamp}-{trace_id}-{request_id}-request.json"
    response_path = artifact_dir / f"{timestamp}-{trace_id}-{request_id}-response.json"
    events_path = artifact_dir / f"{timestamp}-{trace_id}-{request_id}-events.json"
    request_path.write_text(
        json.dumps(audit_payload.get("request_json", {}), indent=2, ensure_ascii=True) + "\n",
        encoding="utf-8",
    )
    events_path.write_text(
        json.dumps(audit_payload.get("events", []), indent=2, ensure_ascii=True) + "\n",
        encoding="utf-8",
    )
    response_json = audit_payload.get("response_json")
    if response_json is not None:
        response_path.write_text(
            json.dumps(response_json, indent=2, ensure_ascii=True) + "\n",
            encoding="utf-8",
        )
        return request_path, response_path
    return request_path, None
