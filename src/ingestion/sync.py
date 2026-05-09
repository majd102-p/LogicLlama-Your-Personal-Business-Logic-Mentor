"""Live source synchronization for public LogicLlama data feeds."""

from __future__ import annotations

import io
import json
import os
import time
import zipfile
from calendar import monthrange
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any
from xml.etree import ElementTree

from requests import HTTPError
from requests import RequestException

from src.core import SQLiteLogicStore

from .adapters import CWEAdapter, KEVAdapter, NVDAdapter, SourceRecord, fetch_json
from .pipeline import LogicIngestionPipeline

NVD_API_URL = "https://services.nvd.nist.gov/rest/json/cves/2.0"
KEV_API_URL = "https://www.cisa.gov/sites/default/files/feeds/known_exploited_vulnerabilities.json"
CWE_ZIP_URL = "https://cwe.mitre.org/data/xml/cwec_v4.20.xml.zip"


@dataclass(frozen=True, slots=True)
class SyncReport:
    source_name: str
    records_fetched: int
    records_ingested: int


class NVDSourceSync:
    """Fetch and normalize CVE records from the NVD API."""

    def __init__(self, api_key: str | None = None) -> None:
        self.api_key = api_key or os.getenv("NVD_API_KEY")
        self.adapter = NVDAdapter()
        self.max_retries = max(0, int(os.getenv("LOGICLLAMA_NVD_MAX_RETRIES", "3")))
        self.retry_backoff_seconds = float(os.getenv("LOGICLLAMA_NVD_RETRY_BACKOFF", "1.0"))

    def fetch(
        self,
        limit: int = 25,
        published_after: datetime | None = None,
        published_before: datetime | None = None,
    ) -> list[SourceRecord]:
        headers = {"apiKey": self.api_key} if self.api_key else None
        records: list[SourceRecord] = []
        start_index = 0
        window_params = self._date_params(published_after=published_after, published_before=published_before)

        while len(records) < limit:
            page_size = min(20, limit - len(records))
            params = {"startIndex": start_index, "resultsPerPage": page_size, **window_params}
            attempts = 0
            payload: dict[str, Any] | None = None
            while attempts <= self.max_retries:
                try:
                    payload = fetch_json(NVD_API_URL, params=params, headers=headers)
                    break
                except HTTPError as exc:
                    response = getattr(exc, "response", None)
                    status_code = getattr(response, "status_code", None)

                    # NVD can throttle high-volume pulls; keep already fetched pages
                    # once retry budget is exhausted.
                    if status_code == 429:
                        if attempts >= self.max_retries:
                            payload = None
                            break
                        attempts += 1
                        time.sleep(self.retry_backoff_seconds * attempts)
                        continue

                    # Retry transient server failures.
                    if status_code is not None and status_code >= 500 and attempts < self.max_retries:
                        attempts += 1
                        time.sleep(self.retry_backoff_seconds * attempts)
                        continue

                    raise
                except RequestException:
                    # Retry transient network errors and keep partial data if retries are exhausted.
                    if attempts >= self.max_retries:
                        payload = None
                        break
                    attempts += 1
                    time.sleep(self.retry_backoff_seconds * attempts)

            if payload is None:
                break
            vulnerabilities = payload.get("vulnerabilities", [])
            if not vulnerabilities:
                break
            for item in vulnerabilities:
                records.append(self.adapter.normalize(item))
                if len(records) >= limit:
                    break
            start_index += len(vulnerabilities)

        return records

    def fetch_history(self, start_year: int = 1999, end_year: int | None = None) -> list[SourceRecord]:
        if end_year is None:
            end_year = datetime.now(timezone.utc).year

        records: list[SourceRecord] = []
        for year in range(start_year, end_year + 1):
            for window_start, window_end in self._year_windows(year):
                records.extend(
                    self.fetch(limit=100000, published_after=window_start, published_before=window_end)
                )
        return records

    @staticmethod
    def _date_params(
        published_after: datetime | None = None,
        published_before: datetime | None = None,
    ) -> dict[str, str]:
        params: dict[str, str] = {}
        if published_after is not None:
            params["pubStartDate"] = NVDSourceSync._to_nvd_iso(published_after)
        if published_before is not None:
            params["pubEndDate"] = NVDSourceSync._to_nvd_iso(published_before)
        return params

    @staticmethod
    def _to_nvd_iso(value: datetime) -> str:
        normalized = value.astimezone(timezone.utc)
        return normalized.strftime("%Y-%m-%dT%H:%M:%S.000")

    @staticmethod
    def _year_windows(year: int) -> list[tuple[datetime, datetime]]:
        windows: list[tuple[datetime, datetime]] = []
        for month in range(1, 13):
            last_day = monthrange(year, month)[1]
            start = datetime(year, month, 1, 0, 0, 0, tzinfo=timezone.utc)
            end = datetime(year, month, last_day, 23, 59, 59, tzinfo=timezone.utc)
            windows.append((start, end))
        return windows


class KEVSourceSync:
    """Fetch and normalize CISA KEV records."""

    def __init__(self) -> None:
        self.adapter = KEVAdapter()

    def fetch(self) -> list[SourceRecord]:
        payload = fetch_json(KEV_API_URL)
        vulnerabilities = payload.get("vulnerabilities", [])
        return [self.adapter.normalize(item) for item in vulnerabilities]


class CWEFeedSync:
    """Fetch and normalize a MITRE CWE XML snapshot."""

    def __init__(self, snapshot_url: str = CWE_ZIP_URL) -> None:
        self.snapshot_url = snapshot_url
        self.adapter = CWEAdapter()

    def fetch(self, limit: int = 100) -> list[SourceRecord]:
        from requests import get

        response = get(self.snapshot_url, timeout=60)
        response.raise_for_status()

        data = response.content
        xml_bytes = self._maybe_unzip(data)
        root = ElementTree.fromstring(xml_bytes)

        namespace = self._namespace(root.tag)
        weaknesses = root.findall(f".//{namespace}Weakness")
        records: list[SourceRecord] = []
        for weakness in weaknesses[:limit]:
            record = self.adapter.normalize(
                {
                    "id": f"CWE-{weakness.attrib.get('ID', 'unknown')}",
                    "name": weakness.attrib.get("Name", "Unknown CWE"),
                    "description": self._extract_description(weakness, namespace),
                }
            )
            records.append(record)
        return records

    @staticmethod
    def _maybe_unzip(data: bytes) -> bytes:
        if data[:2] == b"PK":
            with zipfile.ZipFile(io.BytesIO(data)) as archive:
                xml_members = [name for name in archive.namelist() if name.endswith(".xml")]
                if not xml_members:
                    raise ValueError("CWE archive does not contain XML content")
                return archive.read(xml_members[0])
        return data

    @staticmethod
    def _namespace(tag: str) -> str:
        if tag.startswith("{"):
            return tag.split("}", 1)[0] + "}"
        return ""

    @staticmethod
    def _extract_description(weakness: ElementTree.Element, namespace: str) -> str:
        description = weakness.find(f"{namespace}Description")
        if description is not None and description.text:
            return description.text.strip()
        return weakness.attrib.get("Description", "") or weakness.attrib.get("Name", "Unknown CWE")


class PublicSourceSyncService:
    """Coordinate live public-source ingestion into the local store."""

    def __init__(self, store: SQLiteLogicStore) -> None:
        self.store = store
        self.pipeline = LogicIngestionPipeline(store)

    def sync_nvd(self, limit: int = 25) -> SyncReport:
        records = NVDSourceSync().fetch(limit=limit)
        return self._ingest("nvd", records)

    def sync_nvd_year(self, year: int, limit: int = 500) -> SyncReport:
        records: list[SourceRecord] = []
        sync = NVDSourceSync()
        for start, end in sync._year_windows(year):
            remaining = limit - len(records)
            if remaining <= 0:
                break
            records.extend(sync.fetch(limit=remaining, published_after=start, published_before=end))
        return self._ingest(f"nvd-{year}", records)

    def sync_nvd_history(self, start_year: int = 1999, end_year: int | None = None) -> SyncReport:
        records = NVDSourceSync().fetch_history(start_year=start_year, end_year=end_year)
        return self._ingest("nvd-history", records)

    def sync_kev(self) -> SyncReport:
        records = KEVSourceSync().fetch()
        return self._ingest("kev", records)

    def sync_cwe(self, limit: int = 100) -> SyncReport:
        records = CWEFeedSync().fetch(limit=limit)
        return self._ingest("cwe", records)

    def sync_all(self, nvd_limit: int = 25, cwe_limit: int = 100) -> list[SyncReport]:
        return [
            self.sync_nvd(limit=nvd_limit),
            self.sync_kev(),
            self.sync_cwe(limit=cwe_limit),
        ]

    def _ingest(self, source_name: str, records: list[SourceRecord]) -> SyncReport:
        report = self.pipeline.ingest_source_records(records)
        self.store.record_sync_run(
            source_name=source_name,
            records_fetched=report.files_seen,
            records_ingested=report.cases_written,
            metadata={"mode": "live-sync"},
        )
        return SyncReport(
            source_name=source_name,
            records_fetched=len(records),
            records_ingested=report.cases_written,
        )


def current_utc_iso() -> str:
    return datetime.now(timezone.utc).isoformat()
