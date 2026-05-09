"""Store reporting helpers for LogicLlama."""

from __future__ import annotations

import csv
import io
from dataclasses import dataclass, asdict
from typing import Any

from .models import LogicSource
from .storage import SQLiteLogicStore


@dataclass(frozen=True, slots=True)
class StoreReport:
    case_count: int
    source_count: int
    cases_by_source_type: dict[str, int]
    sources_by_source_type: dict[str, int]
    recent_sources: list[dict[str, Any]]
    recent_sync_runs: list[dict[str, Any]]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def to_text(self) -> str:
        lines = [
            f"Cases: {self.case_count}",
            f"Sources: {self.source_count}",
            "",
            "Cases by source type:",
        ]
        for source_type, count in sorted(self.cases_by_source_type.items()):
            lines.append(f"- {source_type}: {count}")
        lines.append("")
        lines.append("Sources by source type:")
        for source_type, count in sorted(self.sources_by_source_type.items()):
            lines.append(f"- {source_type}: {count}")
        lines.append("")
        lines.append("Recent sources:")
        for source in self.recent_sources:
            lines.append(f"- {source['source_type']} · {source['source_id']} · {source['title']}")
        if self.recent_sync_runs:
            lines.append("")
            lines.append("Recent sync runs:")
            for run in self.recent_sync_runs:
                lines.append(
                    f"- {run['source_name']} · fetched={run['records_fetched']} ingested={run['records_ingested']} · {run['status']}"
                )
        return "\n".join(lines)

    def to_csv(self) -> str:
        buffer = io.StringIO()
        writer = csv.writer(buffer)
        writer.writerow(["section", "key", "value"])
        writer.writerow(["summary", "case_count", self.case_count])
        writer.writerow(["summary", "source_count", self.source_count])
        for source_type, count in sorted(self.cases_by_source_type.items()):
            writer.writerow(["cases_by_source_type", source_type, count])
        for source_type, count in sorted(self.sources_by_source_type.items()):
            writer.writerow(["sources_by_source_type", source_type, count])
        for index, source in enumerate(self.recent_sources, start=1):
            writer.writerow(["recent_sources", index, f"{source['source_type']}|{source['source_id']}|{source['title']}|{source['retrieved_at']}"])
        for index, run in enumerate(self.recent_sync_runs, start=1):
            writer.writerow([
                "recent_sync_runs",
                index,
                f"{run['source_name']}|{run['records_fetched']}|{run['records_ingested']}|{run['status']}|{run['started_at']}",
            ])
        return buffer.getvalue()


def build_store_report(store: SQLiteLogicStore, limit: int = 10) -> StoreReport:
    sources = store.list_sources(limit=limit)
    return StoreReport(
        case_count=store.count_cases(),
        source_count=store.count_sources(),
        cases_by_source_type=store.count_cases_by_source_type(),
        sources_by_source_type=store.count_sources_by_source_type(),
        recent_sources=[_source_to_dict(source) for source in sources],
        recent_sync_runs=store.list_sync_runs(limit=limit),
    )


def _source_to_dict(source: LogicSource) -> dict[str, Any]:
    return {
        "source_id": source.source_id,
        "source_type": source.source_type.value,
        "title": source.title,
        "uri": source.uri,
        "retrieved_at": source.retrieved_at.isoformat(),
    }
