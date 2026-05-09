from datetime import datetime, timezone
from types import SimpleNamespace

import requests

from src.core import SQLiteLogicStore
from src.ingestion.sync import CWEFeedSync, KEVSourceSync, NVDSourceSync, PublicSourceSyncService


def test_nvd_source_sync_fetches_and_normalizes(monkeypatch) -> None:
    calls: list[dict[str, int]] = []

    def fake_fetch_json(url, params=None, headers=None):
        calls.append(params or {})
        return {
            "vulnerabilities": [
                {
                    "cve": {
                        "id": "CVE-2024-0100",
                        "descriptions": [{"lang": "en", "value": "Example auth bypass."}],
                        "weaknesses": [{"description": [{"lang": "en", "value": "CWE-639"}]}],
                        "metrics": {"cvssMetricV31": [{"cvssData": {"baseScore": 9.1}}]},
                    }
                }
            ]
        }

    monkeypatch.setattr("src.ingestion.sync.fetch_json", fake_fetch_json)

    records = NVDSourceSync().fetch(limit=1)

    assert calls == [{"startIndex": 0, "resultsPerPage": 1}]
    assert len(records) == 1
    assert records[0].source.source_id == "CVE-2024-0100"
    assert records[0].case.cwe_ids == ["CWE-639"]


def test_nvd_source_sync_includes_date_filters(monkeypatch) -> None:
    calls: list[dict[str, str]] = []

    def fake_fetch_json(url, params=None, headers=None):
        calls.append(params or {})
        return {"vulnerabilities": []}

    monkeypatch.setattr("src.ingestion.sync.fetch_json", fake_fetch_json)

    records = NVDSourceSync().fetch(
        limit=1,
        published_after=datetime(2024, 1, 1, tzinfo=timezone.utc),
        published_before=datetime(2024, 12, 31, 23, 59, 59, tzinfo=timezone.utc),
    )

    assert records == []
    assert calls == [
        {
            "startIndex": 0,
            "resultsPerPage": 1,
            "pubStartDate": "2024-01-01T00:00:00.000",
            "pubEndDate": "2024-12-31T23:59:59.000",
        }
    ]


def test_nvd_source_sync_advances_by_results_count(monkeypatch) -> None:
    calls: list[dict[str, int]] = []
    pages = [
        {
            "vulnerabilities": [
                {"cve": {"id": "CVE-2024-1000", "descriptions": [{"lang": "en", "value": "First page."}]}} 
            ]
        },
        {
            "vulnerabilities": [
                {"cve": {"id": "CVE-2024-1001", "descriptions": [{"lang": "en", "value": "Second page."}]}} 
            ]
        },
    ]

    def fake_fetch_json(url, params=None, headers=None):
        calls.append(params or {})
        return pages[len(calls) - 1]

    monkeypatch.setattr("src.ingestion.sync.fetch_json", fake_fetch_json)

    records = NVDSourceSync().fetch(limit=2)

    assert calls == [
        {"startIndex": 0, "resultsPerPage": 2},
        {"startIndex": 1, "resultsPerPage": 1},
    ]
    assert [record.source.source_id for record in records] == ["CVE-2024-1000", "CVE-2024-1001"]


def test_nvd_source_sync_returns_partial_on_rate_limit(monkeypatch) -> None:
    calls = 0

    def fake_fetch_json(url, params=None, headers=None):
        nonlocal calls
        calls += 1
        if calls == 1:
            return {
                "vulnerabilities": [
                    {
                        "cve": {
                            "id": "CVE-2024-2000",
                            "descriptions": [{"lang": "en", "value": "First page."}],
                        }
                    }
                ]
            }
        response = requests.Response()
        response.status_code = 429
        raise requests.HTTPError("Too Many Requests", response=response)

    monkeypatch.setattr("src.ingestion.sync.fetch_json", fake_fetch_json)

    records = NVDSourceSync().fetch(limit=40)

    assert len(records) == 1
    assert records[0].source.source_id == "CVE-2024-2000"


def test_nvd_source_sync_retries_transient_network_error(monkeypatch) -> None:
    calls = 0

    def fake_fetch_json(url, params=None, headers=None):
        nonlocal calls
        calls += 1
        if calls == 1:
            raise requests.RequestException("temporary network failure")
        return {
            "vulnerabilities": [
                {
                    "cve": {
                        "id": "CVE-2024-2100",
                        "descriptions": [{"lang": "en", "value": "Recovered after retry."}],
                    }
                }
            ]
        }

    monkeypatch.setattr("src.ingestion.sync.fetch_json", fake_fetch_json)
    monkeypatch.setenv("LOGICLLAMA_NVD_MAX_RETRIES", "2")
    monkeypatch.setattr("src.ingestion.sync.time.sleep", lambda _seconds: None)

    records = NVDSourceSync().fetch(limit=1)

    assert calls == 2
    assert len(records) == 1
    assert records[0].source.source_id == "CVE-2024-2100"


def test_nvd_source_sync_retries_on_server_error(monkeypatch) -> None:
    calls = 0

    def fake_fetch_json(url, params=None, headers=None):
        nonlocal calls
        calls += 1
        if calls == 1:
            response = requests.Response()
            response.status_code = 503
            raise requests.HTTPError("Service unavailable", response=response)
        return {
            "vulnerabilities": [
                {
                    "cve": {
                        "id": "CVE-2024-2200",
                        "descriptions": [{"lang": "en", "value": "Recovered from 5xx."}],
                    }
                }
            ]
        }

    monkeypatch.setattr("src.ingestion.sync.fetch_json", fake_fetch_json)
    monkeypatch.setenv("LOGICLLAMA_NVD_MAX_RETRIES", "2")
    monkeypatch.setattr("src.ingestion.sync.time.sleep", lambda _seconds: None)

    records = NVDSourceSync().fetch(limit=1)

    assert calls == 2
    assert len(records) == 1
    assert records[0].source.source_id == "CVE-2024-2200"


def test_kev_source_sync_fetches_and_normalizes(monkeypatch) -> None:
    def fake_fetch_json(url, params=None, headers=None):
        return {
            "vulnerabilities": [
                {
                    "cveID": "CVE-2024-0200",
                    "shortDescription": "Exploited weakness in access control.",
                    "knownRansomwareCampaignUse": "No",
                }
            ]
        }

    monkeypatch.setattr("src.ingestion.sync.fetch_json", fake_fetch_json)

    records = KEVSourceSync().fetch()

    assert len(records) == 1
    assert records[0].source.source_type.value == "kev"
    assert records[0].case.source_type.value == "kev"


def test_cwe_feed_sync_fetches_and_normalizes(monkeypatch) -> None:
    xml_payload = b"""<?xml version='1.0' encoding='UTF-8'?>
<Weakness_Catalog>
  <Weaknesses>
    <Weakness ID='639' Name='Authorization Bypass Through User-Controlled Key'>
      <Description>A user-controlled key may expose another user's object.</Description>
    </Weakness>
  </Weaknesses>
</Weakness_Catalog>
"""

    monkeypatch.setattr(
        "requests.get",
        lambda *args, **kwargs: SimpleNamespace(content=xml_payload, raise_for_status=lambda: None),
    )

    records = CWEFeedSync(snapshot_url="https://example.invalid/cwe.xml").fetch(limit=1)

    assert len(records) == 1
    assert records[0].source.source_id == "CWE-639"
    assert records[0].case.cwe_ids == ["CWE-639"]


def test_public_source_sync_service_persists_records(monkeypatch, tmp_path) -> None:
    store = SQLiteLogicStore(tmp_path / "logicllama.sqlite3")
    store.initialize()

    monkeypatch.setattr(
        "src.ingestion.sync.NVDSourceSync.fetch",
        lambda self, limit=25: [
            NVDSourceSync().adapter.normalize(
                {
                    "cve": {
                        "id": "CVE-2024-0300",
                        "descriptions": [{"lang": "en", "value": "Sample feed item."}],
                        "weaknesses": [{"description": [{"lang": "en", "value": "CWE-840"}]}],
                    }
                }
            )
        ],
    )
    monkeypatch.setattr(
        "src.ingestion.sync.KEVSourceSync.fetch",
        lambda self: [
            KEVSourceSync().adapter.normalize(
                {"cveID": "CVE-2024-0400", "shortDescription": "Known exploited.", "knownRansomwareCampaignUse": "No"}
            )
        ],
    )
    monkeypatch.setattr(
        "src.ingestion.sync.CWEFeedSync.fetch",
        lambda self, limit=100: [
            CWEFeedSync(snapshot_url="https://example.invalid/cwe.xml").adapter.normalize(
                {"id": "CWE-639", "name": "Authorization Bypass Through User-Controlled Key", "description": "Example."}
            )
        ],
    )

    reports = PublicSourceSyncService(store).sync_all(nvd_limit=1, cwe_limit=1)

    assert [report.source_name for report in reports] == ["nvd", "kev", "cwe"]
    assert len(store.list_cases()) == 3
    assert store.count_cases_by_source_type() == {"cwe": 1, "kev": 1, "nvd": 1}
    assert store.count_sources_by_source_type() == {"cwe": 1, "kev": 1, "nvd": 1}
    assert len(store.list_sources()) == 3
    assert len(store.list_sync_runs()) == 3
    assert {run["source_name"] for run in store.list_sync_runs()} == {"nvd", "kev", "cwe"}


def test_public_source_sync_service_historical_nvd(monkeypatch, tmp_path) -> None:
    store = SQLiteLogicStore(tmp_path / "logicllama.sqlite3")
    store.initialize()

    monkeypatch.setattr(
        "src.ingestion.sync.NVDSourceSync.fetch_history",
        lambda self, start_year=1999, end_year=None: [
            NVDSourceSync().adapter.normalize(
                {
                    "cve": {
                        "id": "CVE-2024-9998",
                        "descriptions": [{"lang": "en", "value": "Historical NVD record."}],
                        "weaknesses": [{"description": [{"lang": "en", "value": "CWE-841"}]}],
                    }
                }
            )
        ],
    )

    report = PublicSourceSyncService(store).sync_nvd_history(start_year=2024, end_year=2024)

    assert report.source_name == "nvd-history"
    assert report.records_fetched == 1
    assert report.records_ingested == 1
    assert len(store.list_cases()) == 1
    assert store.list_cases()[0].source_type.value == "nvd"
