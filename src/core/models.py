"""Typed domain models for the first LogicLlama release."""

from __future__ import annotations

from datetime import datetime, timezone
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator


class LogicSourceType(StrEnum):
    """Source family for imported evidence."""

    NVD = "nvd"
    CWE = "cwe"
    KEV = "kev"
    OWASP = "owasp"
    PORTSWIGGER = "portswigger"
    LOCAL = "local"


class LogicCaseStatus(StrEnum):
    """Lifecycle status for normalized cases."""

    draft = "draft"
    validated = "validated"
    production = "production"


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class LogicSource(BaseModel):
    """Provenance record for a source document or feed item."""

    model_config = ConfigDict(extra="forbid")

    source_id: str = Field(min_length=1)
    source_type: LogicSourceType
    title: str = Field(min_length=1)
    uri: str = Field(min_length=1)
    retrieved_at: datetime = Field(default_factory=utcnow)
    license: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class LogicSignal(BaseModel):
    """Behavioral signal derived from a source or test run."""

    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1)
    value: str | float | bool
    confidence: float = Field(ge=0.0, le=1.0)
    description: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class LogicStep(BaseModel):
    """Observed or inferred workflow step."""

    model_config = ConfigDict(extra="forbid")

    step_id: str = Field(min_length=1)
    order: int = Field(ge=0)
    title: str = Field(min_length=1)
    state_before: str | None = None
    state_after: str | None = None
    notes: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class EvidenceItem(BaseModel):
    """Evidence tied to a case, step, or signal."""

    model_config = ConfigDict(extra="forbid")

    evidence_id: str = Field(min_length=1)
    summary: str = Field(min_length=1)
    source_id: str | None = None
    evidence_type: str = Field(default="observation")
    metadata: dict[str, Any] = Field(default_factory=dict)


class QueryFilter(BaseModel):
    """Deterministic search filter used by the first retrieval layer."""

    model_config = ConfigDict(extra="forbid")

    text: str | None = None
    source_type: LogicSourceType | None = None
    cwe_id: str | None = None
    keyword: str | None = None
    limit: int = Field(default=20, ge=1, le=100)

    @field_validator("text", "cwe_id", "keyword")
    @classmethod
    def strip_empty(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip()
        return normalized or None


class LogicCase(BaseModel):
    """Canonical record for a business-logic pattern."""

    model_config = ConfigDict(extra="forbid")

    pattern_id: str = Field(min_length=1)
    title: str = Field(min_length=1)
    focus: str = Field(min_length=1)
    summary: str = Field(min_length=1)
    source_type: LogicSourceType = LogicSourceType.LOCAL
    source_ids: list[str] = Field(default_factory=list)
    cwe_ids: list[str] = Field(default_factory=list)
    keywords: list[str] = Field(default_factory=list)
    signals: list[LogicSignal] = Field(default_factory=list)
    workflow_steps: list[LogicStep] = Field(default_factory=list)
    evidence: list[EvidenceItem] = Field(default_factory=list)
    status: LogicCaseStatus = LogicCaseStatus.draft
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)

    @field_validator("source_ids", "cwe_ids", "keywords")
    @classmethod
    def normalize_strings(cls, values: list[str]) -> list[str]:
        normalized = [value.strip() for value in values if value and value.strip()]
        return normalized
