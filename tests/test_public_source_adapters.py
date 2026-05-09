from src.ingestion import CWEAdapter, KEVAdapter, NVDAdapter


def test_nvd_adapter_normalizes_record() -> None:
    adapter = NVDAdapter()
    record = adapter.normalize(
        {
            "cve": {
                "id": "CVE-2024-0001",
                "descriptions": [{"lang": "en", "value": "Example auth bypass in checkout flow."}],
                "weaknesses": [{"description": [{"lang": "en", "value": "CWE-840"}]}],
                "metrics": {"cvssMetricV31": [{"cvssData": {"baseScore": 8.8}}]},
            }
        }
    )

    assert record.source.source_id == "CVE-2024-0001"
    assert record.source.source_type.value == "nvd"
    assert record.case.cwe_ids == ["CWE-840"]
    assert record.case.status.value == "validated"
    assert record.case.confidence == 0.9


def test_kev_adapter_normalizes_record() -> None:
    adapter = KEVAdapter()
    record = adapter.normalize(
        {
            "cveID": "CVE-2024-0002",
            "shortDescription": "Known exploited weakness in access control.",
            "knownRansomwareCampaignUse": "No",
        }
    )

    assert record.source.source_id == "CVE-2024-0002"
    assert record.source.source_type.value == "kev"
    assert record.case.keywords == ["exploited", "kev", "priority"]
    assert record.case.confidence == 1.0


def test_cwe_adapter_normalizes_record() -> None:
    adapter = CWEAdapter()
    record = adapter.normalize(
        {
            "id": "CWE-639",
            "name": "Authorization Bypass Through User-Controlled Key",
            "description": "A user-controlled key can be used to access another user's data.",
        }
    )

    assert record.source.source_id == "CWE-639"
    assert record.case.cwe_ids == ["CWE-639"]
    assert record.case.focus == "Weakness Taxonomy"
    assert record.case.status.value == "validated"
