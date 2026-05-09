"""Typed projection model for the MASTER_SCHEMA document shape."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class MasterSchemaProjection(BaseModel):
    """Validated runtime representation of the MASTER_SCHEMA export."""

    model_config = ConfigDict(extra="forbid")

    schema_version: str
    pattern_id: str
    metadata: dict[str, Any]
    title: str
    focus: str
    search_index: dict[str, Any]
    core_concept: dict[str, Any]
    logic_flow: dict[str, Any]
    attack_model: dict[str, Any]
    developer_mindset: dict[str, Any]
    data_points: dict[str, Any]
    comparative_analysis: list[dict[str, Any]] = Field(default_factory=list)
    training: dict[str, Any]
    user_feedback: dict[str, Any]
    arsenal: dict[str, Any]
    impact: dict[str, Any]
    graph_relations: dict[str, Any]
    detection: dict[str, Any]
    mitigation: dict[str, Any]
    execution_context: dict[str, Any]
    timing: dict[str, Any]
    ai_features: dict[str, Any]
    risk_score: dict[str, Any]
    real_world_mapping: list[dict[str, Any]]
    simulation: dict[str, Any]
    inference_rules: list[dict[str, Any]] = Field(default_factory=list)
    decision_logic: dict[str, Any]