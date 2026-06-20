"""LLM schema constants."""

from __future__ import annotations

SEMANTIC_REVIEW_SCHEMA = {
    "name": "semantic_review_result",
    "schema": {
        "type": "object",
        "additionalProperties": False,
        "required": ["decision", "summary", "reviewer_ref", "model", "findings"],
        "properties": {
            "decision": {
                "type": "string",
                "enum": ["passed", "failed", "needs_revision"],
            },
            "summary": {"type": "string"},
            "reviewer_ref": {"type": "string"},
            "model": {"type": ["string", "null"]},
            "counterexamples": {
                "type": "array",
                "items": {"type": "string"},
            },
            "findings": {
                "type": "array",
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "required": ["severity", "code", "message", "evidence", "details"],
                    "properties": {
                        "severity": {"type": "string"},
                        "code": {"type": "string"},
                        "message": {"type": "string"},
                        "evidence": {
                            "type": "array",
                            "items": {"type": "string"},
                        },
                        "details": {
                            "type": "object",
                            "additionalProperties": True,
                        },
                    },
                },
            },
        },
    },
    "strict": True,
}

SUBMISSION_INTENT_SCHEMA = {
    "name": "submission_intent_result",
    "schema": {
        "type": "object",
        "additionalProperties": False,
        "required": [
            "intent",
            "summary",
            "reviewer_ref",
            "model",
            "confidence",
            "matched_signals",
            "reasoning",
            "suggested_action",
        ],
        "properties": {
            "intent": {
                "type": "string",
                "enum": ["maintainer_publish", "downstream_submit", "ambiguous"],
            },
            "summary": {"type": "string"},
            "reviewer_ref": {"type": "string"},
            "model": {"type": ["string", "null"]},
            "confidence": {"type": "string", "enum": ["low", "medium", "high"]},
            "matched_signals": {
                "type": "array",
                "items": {"type": "string"},
            },
            "reasoning": {
                "type": "array",
                "items": {"type": "string"},
            },
            "suggested_action": {"type": ["string", "null"]},
        },
    },
    "strict": True,
}
