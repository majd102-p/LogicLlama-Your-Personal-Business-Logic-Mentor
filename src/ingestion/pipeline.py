"""Structured ingestion for canonical LogicLlama records."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from pydantic import BaseModel, ConfigDict

from src.core import LogicCase, LogicSource, SQLiteLogicStore
from src.ingestion.adapters import SourceRecord


class FixtureDocument(BaseModel):
    """Minimal JSON document used by the first ingestion flow."""

    model_config = ConfigDict(extra="forbid")

    source: LogicSource
    case: LogicCase


@dataclass(frozen=True, slots=True)
class IngestionReport:
    files_seen: int
    sources_written: int
    cases_written: int


class LogicIngestionPipeline:
    """Load fixture documents and persist their canonical records."""

    def __init__(self, store: SQLiteLogicStore) -> None:
        self.store = store

    def ingest_directory(self, directory: Path) -> IngestionReport:
        files_seen = 0
        sources_written = 0
        cases_written = 0

        for fixture_path in sorted(Path(directory).glob("*.json")):
            files_seen += 1
            document = self._load_fixture(fixture_path)
            self._persist_document(document.source, document.case)
            sources_written += 1
            cases_written += 1

        return IngestionReport(
            files_seen=files_seen,
            sources_written=sources_written,
            cases_written=cases_written,
        )

    @staticmethod
    def ingest_file(store: SQLiteLogicStore, fixture_path: Path) -> IngestionReport:
        pipeline = LogicIngestionPipeline(store)
        document = pipeline._load_fixture(fixture_path)
        pipeline._persist_document(document.source, document.case)
        return IngestionReport(files_seen=1, sources_written=1, cases_written=1)

    def ingest_source_records(self, records: list[SourceRecord]) -> IngestionReport:
        for record in records:
            self._persist_document(record.source, record.case)
        return IngestionReport(
            files_seen=len(records),
            sources_written=len(records),
            cases_written=len(records),
        )

    @staticmethod
    def _load_fixture(fixture_path: Path) -> FixtureDocument:
        with Path(fixture_path).open("r", encoding="utf-8") as handle:
            payload = json.load(handle)
        return FixtureDocument.model_validate(payload)

    def _persist_document(self, source: LogicSource, case: LogicCase) -> None:
        self.store.upsert_source(source)
        normalized_case = case.model_copy(update={"source_type": source.source_type})
        self.store.upsert_case(normalized_case)


def ingest_fixture_directory(store: SQLiteLogicStore, directory: Path) -> IngestionReport:
    return LogicIngestionPipeline(store).ingest_directory(directory)
