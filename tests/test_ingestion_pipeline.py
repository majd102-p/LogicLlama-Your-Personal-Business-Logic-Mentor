from pathlib import Path

from src.core import LogicCaseStatus, SQLiteLogicStore, get_settings
from src.ingestion import LogicIngestionPipeline, ingest_fixture_directory
from src.rag import LogicSearchService


def test_fixture_ingestion_and_search(tmp_path: Path) -> None:
    settings = get_settings()
    database_path = tmp_path / "logicllama.sqlite3"
    store = SQLiteLogicStore(database_path)
    store.initialize()

    fixture_dir = tmp_path / "fixtures"
    fixture_dir.mkdir()
    fixture_source = settings.fixture_dir / "portswigger_access_control_reference.json"
    fixture_target = fixture_dir / fixture_source.name
    fixture_target.write_text(fixture_source.read_text(encoding="utf-8"), encoding="utf-8")

    pipeline = LogicIngestionPipeline(store)
    report = pipeline.ingest_directory(fixture_dir)

    assert report.files_seen == 1
    assert report.sources_written == 1
    assert report.cases_written == 1

    cases = store.list_cases()
    assert len(cases) == 1
    assert cases[0].pattern_id == "LOGIC-ACCESS-001"
    assert cases[0].status == LogicCaseStatus.validated
    assert cases[0].source_type.value == "portswigger"

    search = LogicSearchService(store)
    results = search.search("access control", limit=10)

    assert len(results) == 1
    assert results[0].pattern_id == "LOGIC-ACCESS-001"
    assert results[0].cwe_ids == ["CWE-639", "CWE-841"]


def test_owasp_fixture_ingestion(tmp_path: Path) -> None:
    settings = get_settings()
    database_path = tmp_path / "logicllama.sqlite3"
    store = SQLiteLogicStore(database_path)
    store.initialize()

    fixture_dir = tmp_path / "fixtures"
    fixture_dir.mkdir()
    fixture_source = settings.fixture_dir / "owasp_top_ten_reference.json"
    fixture_target = fixture_dir / fixture_source.name
    fixture_target.write_text(fixture_source.read_text(encoding="utf-8"), encoding="utf-8")

    pipeline = LogicIngestionPipeline(store)
    report = pipeline.ingest_directory(fixture_dir)

    assert report.files_seen == 1
    assert report.sources_written == 1
    assert report.cases_written == 1

    cases = store.list_cases()
    assert len(cases) == 1
    assert cases[0].pattern_id == "LOGIC-OWASP-001"
    assert cases[0].source_type.value == "owasp"
    assert cases[0].cwe_ids == ["CWE-284"]

    search = LogicSearchService(store)
    results = search.search("top ten", limit=10)

    assert len(results) == 1
    assert results[0].pattern_id == "LOGIC-OWASP-001"
    assert results[0].focus == "Reference Framework"


def test_mixed_fixture_ingestion_preserves_source_families(tmp_path: Path) -> None:
    settings = get_settings()
    database_path = tmp_path / "logicllama.sqlite3"
    store = SQLiteLogicStore(database_path)
    store.initialize()

    fixture_dir = tmp_path / "fixtures"
    fixture_dir.mkdir()
    for fixture_name in [
        "portswigger_access_control_reference.json",
        "portswigger_business_logic_reference.json",
        "owasp_top_ten_reference.json",
    ]:
        fixture_source = settings.fixture_dir / fixture_name
        fixture_target = fixture_dir / fixture_source.name
        fixture_target.write_text(fixture_source.read_text(encoding="utf-8"), encoding="utf-8")

    pipeline = LogicIngestionPipeline(store)
    report = pipeline.ingest_directory(fixture_dir)

    assert report.files_seen == 3
    assert report.sources_written == 3
    assert report.cases_written == 3

    cases = sorted(store.list_cases(), key=lambda case: case.pattern_id)
    assert [case.pattern_id for case in cases] == ["LOGIC-ACCESS-001", "LOGIC-OWASP-001", "LOGIC-PS-002"]
    assert [case.source_type.value for case in cases] == ["portswigger", "owasp", "portswigger"]

    search = LogicSearchService(store)
    assert search.search("access control", limit=10)[0].pattern_id == "LOGIC-ACCESS-001"
    assert search.search("business logic", limit=10)[0].pattern_id == "LOGIC-PS-002"
