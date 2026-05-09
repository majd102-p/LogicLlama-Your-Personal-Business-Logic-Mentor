"""Tests for the validated MASTER_SCHEMA projection model."""

from __future__ import annotations

from src.core.master_schema import MasterSchemaProjection
from src.core.models import LogicCase, LogicSource, LogicSourceType
from src.core.schema_projection import build_master_schema_projection


def test_master_schema_projection_validates_export_shape() -> None:
    source = LogicSource(
        source_id="local_sample",
        source_type=LogicSourceType.LOCAL,
        title="Local Sample",
        uri="https://example.invalid/sample",
    )
    logic_case = LogicCase(
        pattern_id="LOGIC-MASTER-001",
        title="Master schema test case",
        focus="Access Control",
        summary="Validation case for the MASTER_SCHEMA projection.",
        source_ids=[source.source_id],
        cwe_ids=["CWE-639"],
        keywords=["projection", "schema"],
    )

    payload = build_master_schema_projection(logic_case, source)
    projection = MasterSchemaProjection.model_validate(payload)

    assert projection.schema_version == "1.0.0"
    assert projection.pattern_id == logic_case.pattern_id
    assert projection.search_index["entities"] == [source.source_id, "CWE-639"]
    assert projection.decision_logic["priority_signals"]