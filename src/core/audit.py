"""Project audit helpers for alignment between docs and implementation."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from .models import LogicCase, LogicSource


@dataclass(frozen=True, slots=True)
class ProjectAuditReport:
    master_schema_path: str
    tool_mapping_path: str
    schema_required_fields: list[str]
    implemented_case_fields: list[str]
    implemented_source_fields: list[str]
    covered_schema_fields: list[str]
    missing_schema_fields: list[str]
    tool_mapping_sections: list[str]
    notes: list[str]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def to_text(self) -> str:
        lines = [
            f"Master schema: {self.master_schema_path}",
            f"Tool mapping: {self.tool_mapping_path}",
            "",
            f"Schema required fields: {len(self.schema_required_fields)}",
            f"Implemented case fields: {len(self.implemented_case_fields)}",
            f"Implemented source fields: {len(self.implemented_source_fields)}",
            f"Covered schema fields: {len(self.covered_schema_fields)}",
            f"Missing schema fields: {len(self.missing_schema_fields)}",
            "",
            "Covered schema fields:",
        ]
        lines.extend(f"- {field}" for field in self.covered_schema_fields)
        lines.append("")
        lines.append("Missing schema fields:")
        lines.extend(f"- {field}" for field in self.missing_schema_fields)
        lines.append("")
        lines.append("Tool mapping sections:")
        lines.extend(f"- {section}" for section in self.tool_mapping_sections)
        if self.notes:
            lines.append("")
            lines.append("Notes:")
            lines.extend(f"- {note}" for note in self.notes)
        return "\n".join(lines)


def build_project_audit(project_root: Path) -> ProjectAuditReport:
    docs_dir = project_root / "docs"
    master_schema_path = docs_dir / "MASTER_SCHEMA.json"
    tool_mapping_path = docs_dir / "TOOL_MAPPING.json"

    master_schema = json.loads(master_schema_path.read_text(encoding="utf-8"))
    tool_mapping = json.loads(tool_mapping_path.read_text(encoding="utf-8"))

    schema_required_fields = list(master_schema.get("required", []))
    implemented_case_fields = list(LogicCase.model_fields.keys())
    implemented_source_fields = list(LogicSource.model_fields.keys())

    covered_schema_fields = sorted(
        field for field in schema_required_fields if field in implemented_case_fields or field in implemented_source_fields
    )
    missing_schema_fields = sorted(set(schema_required_fields) - set(covered_schema_fields))
    tool_mapping_sections = sorted(tool_mapping.keys())

    notes = [
        "The runtime currently implements the LogicCase/LogicSource milestone, not the full aspirational master schema.",
        "Most missing schema fields are future-planned research metadata, attack modeling, and simulation layers.",
        "Tool mapping is configuration-only in the current release; there is no autonomous offensive execution layer.",
    ]

    return ProjectAuditReport(
        master_schema_path=str(master_schema_path),
        tool_mapping_path=str(tool_mapping_path),
        schema_required_fields=schema_required_fields,
        implemented_case_fields=implemented_case_fields,
        implemented_source_fields=implemented_source_fields,
        covered_schema_fields=covered_schema_fields,
        missing_schema_fields=missing_schema_fields,
        tool_mapping_sections=tool_mapping_sections,
        notes=notes,
    )
