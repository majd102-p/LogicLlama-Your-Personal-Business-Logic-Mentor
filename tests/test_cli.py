from pathlib import Path
import json
from types import SimpleNamespace

from src.core.cli import main


def test_cli_ingest_fixtures(monkeypatch, tmp_path, capsys) -> None:
    fixture_dir = tmp_path / "fixtures"
    fixture_dir.mkdir()
    fixture_dir.joinpath("sample.json").write_text(
        """{
  "source": {
    "source_id": "local_sample",
    "source_type": "local",
    "title": "Local Sample",
    "uri": "https://example.invalid/sample",
    "metadata": {}
  },
  "case": {
    "pattern_id": "LOGIC-LOCAL-001",
    "title": "Sample local logic case",
    "focus": "Access Control",
    "summary": "Local fixture for CLI testing.",
    "source_ids": ["local_sample"],
    "cwe_ids": ["CWE-639"],
    "keywords": ["sample"],
    "signals": [],
    "workflow_steps": [],
    "evidence": [],
    "status": "validated",
    "confidence": 0.8,
    "metadata": {}
  }
}
""",
        encoding="utf-8",
    )

    monkeypatch.setenv("LOGICLLAMA_DB_PATH", str(tmp_path / "logicllama.sqlite3"))
    monkeypatch.setenv("LOGICLLAMA_FIXTURE_DIR", str(fixture_dir))

    exit_code = main(["ingest-fixtures"])
    output = capsys.readouterr().out

    assert exit_code == 0
    assert "ingested fixtures:" in output


def test_cli_report_exports_json(monkeypatch, tmp_path, capsys) -> None:
    fixture_dir = tmp_path / "fixtures"
    fixture_dir.mkdir()
    fixture_dir.joinpath("sample.json").write_text(
        """{
  "source": {
    "source_id": "local_sample",
    "source_type": "local",
    "title": "Local Sample",
    "uri": "https://example.invalid/sample",
    "metadata": {}
  },
  "case": {
    "pattern_id": "LOGIC-LOCAL-001",
    "title": "Sample local logic case",
    "focus": "Access Control",
    "summary": "Local fixture for CLI testing.",
    "source_ids": ["local_sample"],
    "cwe_ids": ["CWE-639"],
    "keywords": ["sample"],
    "signals": [],
    "workflow_steps": [],
    "evidence": [],
    "status": "validated",
    "confidence": 0.8,
    "metadata": {}
  }
}
""",
        encoding="utf-8",
    )

    monkeypatch.setenv("LOGICLLAMA_DB_PATH", str(tmp_path / "logicllama.sqlite3"))
    monkeypatch.setenv("LOGICLLAMA_FIXTURE_DIR", str(fixture_dir))

    ingest_exit = main(["ingest-fixtures"])
    assert ingest_exit == 0
    capsys.readouterr()

    report_exit = main(["report", "--limit", "5"])
    output = capsys.readouterr().out

    payload = json.loads(output)

    assert report_exit == 0
    assert payload["case_count"] == 1
    assert payload["source_count"] == 1
    assert payload["cases_by_source_type"] == {"local": 1}
    assert payload["sources_by_source_type"] == {"local": 1}
    assert payload["recent_sources"][0]["source_id"] == "local_sample"
    assert payload["recent_sync_runs"] == []


def test_cli_report_exports_text(monkeypatch, tmp_path, capsys) -> None:
    fixture_dir = tmp_path / "fixtures"
    fixture_dir.mkdir()
    fixture_dir.joinpath("sample.json").write_text(
        """{
  "source": {
    "source_id": "local_sample",
    "source_type": "local",
    "title": "Local Sample",
    "uri": "https://example.invalid/sample",
    "metadata": {}
  },
  "case": {
    "pattern_id": "LOGIC-LOCAL-001",
    "title": "Sample local logic case",
    "focus": "Access Control",
    "summary": "Local fixture for CLI testing.",
    "source_ids": ["local_sample"],
    "cwe_ids": ["CWE-639"],
    "keywords": ["sample"],
    "signals": [],
    "workflow_steps": [],
    "evidence": [],
    "status": "validated",
    "confidence": 0.8,
    "metadata": {}
  }
}
""",
        encoding="utf-8",
    )

    monkeypatch.setenv("LOGICLLAMA_DB_PATH", str(tmp_path / "logicllama.sqlite3"))
    monkeypatch.setenv("LOGICLLAMA_FIXTURE_DIR", str(fixture_dir))

    ingest_exit = main(["ingest-fixtures"])
    assert ingest_exit == 0
    capsys.readouterr()

    report_exit = main(["report", "--format", "text"])
    output = capsys.readouterr().out

    assert report_exit == 0
    assert "Cases: 1" in output
    assert "Sources: 1" in output
    assert "- local: 1" in output


def test_cli_report_includes_sync_runs(monkeypatch, tmp_path, capsys) -> None:
    fixture_dir = tmp_path / "fixtures"
    fixture_dir.mkdir()
    fixture_dir.joinpath("sample.json").write_text(
        """{
  "source": {
    "source_id": "local_sample",
    "source_type": "local",
    "title": "Local Sample",
    "uri": "https://example.invalid/sample",
    "metadata": {}
  },
  "case": {
    "pattern_id": "LOGIC-LOCAL-001",
    "title": "Sample local logic case",
    "focus": "Access Control",
    "summary": "Local fixture for CLI testing.",
    "source_ids": ["local_sample"],
    "cwe_ids": ["CWE-639"],
    "keywords": ["sample"],
    "signals": [],
    "workflow_steps": [],
    "evidence": [],
    "status": "validated",
    "confidence": 0.8,
    "metadata": {}
  }
}
""",
        encoding="utf-8",
    )

    monkeypatch.setenv("LOGICLLAMA_DB_PATH", str(tmp_path / "logicllama.sqlite3"))
    monkeypatch.setenv("LOGICLLAMA_FIXTURE_DIR", str(fixture_dir))

    ingest_exit = main(["ingest-fixtures"])
    assert ingest_exit == 0
    capsys.readouterr()

    def fake_fetch_json(url, params=None, headers=None):
      return {
        "vulnerabilities": [
          {
            "cve": {
              "id": "CVE-2024-9999",
              "descriptions": [{"lang": "en", "value": "Example sync item."}],
              "weaknesses": [{"description": [{"lang": "en", "value": "CWE-639"}]}],
            }
          }
        ]
      }

    monkeypatch.setattr("src.ingestion.sync.fetch_json", fake_fetch_json)

    sync_exit = main(["sync", "--nvd-limit", "1", "--skip-kev", "--skip-cwe"])
    assert sync_exit == 0
    capsys.readouterr()

    report_exit = main(["report", "--format", "json"])
    output = capsys.readouterr().out

    payload = json.loads(output)

    assert report_exit == 0
    assert payload["recent_sync_runs"][0]["source_name"] == "nvd"


def test_cli_report_exports_csv(monkeypatch, tmp_path, capsys) -> None:
    fixture_dir = tmp_path / "fixtures"
    fixture_dir.mkdir()
    fixture_dir.joinpath("sample.json").write_text(
        """{
  "source": {
    "source_id": "local_sample",
    "source_type": "local",
    "title": "Local Sample",
    "uri": "https://example.invalid/sample",
    "metadata": {}
  },
  "case": {
    "pattern_id": "LOGIC-LOCAL-001",
    "title": "Sample local logic case",
    "focus": "Access Control",
    "summary": "Local fixture for CLI testing.",
    "source_ids": ["local_sample"],
    "cwe_ids": ["CWE-639"],
    "keywords": ["sample"],
    "signals": [],
    "workflow_steps": [],
    "evidence": [],
    "status": "validated",
    "confidence": 0.8,
    "metadata": {}
  }
}
""",
        encoding="utf-8",
    )

    monkeypatch.setenv("LOGICLLAMA_DB_PATH", str(tmp_path / "logicllama.sqlite3"))
    monkeypatch.setenv("LOGICLLAMA_FIXTURE_DIR", str(fixture_dir))

    ingest_exit = main(["ingest-fixtures"])
    assert ingest_exit == 0
    capsys.readouterr()

    report_exit = main(["report", "--format", "csv"])
    output = capsys.readouterr().out

    assert report_exit == 0
    assert "section,key,value" in output
    assert "summary,case_count,1" in output
    assert "recent_sources,1,local|local_sample|Local Sample" in output
def test_cli_refresh_all_runs_integrated_workflow(monkeypatch, tmp_path, capsys) -> None:
    fixture_dir = tmp_path / "fixtures"
    fixture_dir.mkdir()
    fixture_dir.joinpath("sample.json").write_text(
        """{
  "source": {
    "source_id": "local_sample",
    "source_type": "local",
    "title": "Local Sample",
    "uri": "https://example.invalid/sample",
    "metadata": {}
  },
  "case": {
    "pattern_id": "LOGIC-LOCAL-001",
    "title": "Sample local logic case",
    "focus": "Access Control",
    "summary": "Local fixture for CLI testing.",
    "source_ids": ["local_sample"],
    "cwe_ids": ["CWE-639"],
    "keywords": ["sample"],
    "signals": [],
    "workflow_steps": [],
    "evidence": [],
    "status": "validated",
    "confidence": 0.8,
    "metadata": {}
  }
}
""",
        encoding="utf-8",
    )

    monkeypatch.setenv("LOGICLLAMA_DB_PATH", str(tmp_path / "logicllama.sqlite3"))
    monkeypatch.setenv("LOGICLLAMA_FIXTURE_DIR", str(fixture_dir))

    monkeypatch.setattr(
        "src.core.cli.PublicSourceSyncService.sync_nvd",
        lambda self, limit=25: SimpleNamespace(source_name="nvd", records_fetched=1, records_ingested=1),
    )
    monkeypatch.setattr(
        "src.core.cli.PublicSourceSyncService.sync_kev",
        lambda self: SimpleNamespace(source_name="kev", records_fetched=1, records_ingested=1),
    )
    monkeypatch.setattr(
        "src.core.cli.PublicSourceSyncService.sync_cwe",
        lambda self, limit=100: SimpleNamespace(source_name="cwe", records_fetched=1, records_ingested=1),
    )
    monkeypatch.setattr(
        "src.core.cli.PublicSourceSyncService.sync_nvd_history",
        lambda self, start_year=1999, end_year=None: SimpleNamespace(
            source_name="nvd-history", records_fetched=1, records_ingested=1
        ),
    )

    monkeypatch.setattr(
        "src.ingestion.archive_cwe_snapshots.run_archive",
        lambda output_dir: {"downloaded": 1, "total": 1},
    )
    monkeypatch.setattr(
        "src.ingestion.archive_kev_snapshots.run_archive",
        lambda output_dir: {"downloaded": 1, "total": 1},
    )
    monkeypatch.setattr(
        "src.ingestion.curate_owasp_editions.run_curation",
        lambda output_dir: {"created": 6, "total": 6},
    )

    exit_code = main(["refresh-all", "--history-start-year", "2024", "--history-end-year", "2024"])
    output = capsys.readouterr().out

    assert exit_code == 0
    assert "fixtures:" in output
    assert "nvd: fetched=1 ingested=1" in output
    assert "nvd-history: fetched=1 ingested=1" in output
    assert "cwe-archive: downloaded=1/1" in output
    assert "kev-archive: downloaded=1/1" in output
    assert "owasp-editions: created=6/6" in output


def test_cli_audit_reports_schema_gap(monkeypatch, tmp_path, capsys) -> None:
    monkeypatch.setenv("LOGICLLAMA_DB_PATH", str(tmp_path / "logicllama.sqlite3"))
    exit_code = main(["audit", "--format", "json"])
    output = capsys.readouterr().out

    payload = json.loads(output)

    assert exit_code == 0
    assert payload["master_schema_path"].endswith("docs\\MASTER_SCHEMA.json")
    assert payload["tool_mapping_path"].endswith("docs\\TOOL_MAPPING.json")
    assert "pattern_id" in payload["covered_schema_fields"]
    assert "search_index" in payload["missing_schema_fields"]
    assert "decision_logic" in payload["missing_schema_fields"]


def test_cli_export_schema_projects_case(monkeypatch, tmp_path, capsys) -> None:
    fixture_dir = tmp_path / "fixtures"
    fixture_dir.mkdir()
    fixture_dir.joinpath("sample.json").write_text(
        """{
  "source": {
    "source_id": "local_sample",
    "source_type": "local",
    "title": "Local Sample",
    "uri": "https://example.invalid/sample",
    "metadata": {}
  },
  "case": {
    "pattern_id": "LOGIC-LOCAL-001",
    "title": "Sample local logic case",
    "focus": "Access Control",
    "summary": "Local fixture for CLI testing.",
    "source_ids": ["local_sample"],
    "cwe_ids": ["CWE-639"],
    "keywords": ["sample"],
    "signals": [],
    "workflow_steps": [],
    "evidence": [],
    "status": "validated",
    "confidence": 0.8,
    "metadata": {}
  }
}
""",
        encoding="utf-8",
    )

    monkeypatch.setenv("LOGICLLAMA_DB_PATH", str(tmp_path / "logicllama.sqlite3"))
    monkeypatch.setenv("LOGICLLAMA_FIXTURE_DIR", str(fixture_dir))

    ingest_exit = main(["ingest-fixtures"])
    assert ingest_exit == 0
    capsys.readouterr()

    export_exit = main(["export-schema", "LOGIC-LOCAL-001", "--format", "json"])
    output = capsys.readouterr().out
    payload = json.loads(output)

    assert export_exit == 0
    assert payload["schema_version"] == "1.0.0"
    assert payload["pattern_id"] == "LOGIC-LOCAL-001"
    assert payload["focus"] == "Access Control"
    assert payload["search_index"]["entities"] == ["local_sample", "CWE-639"]
    assert payload["graph_relations"]["nodes"][0] == "LOGIC-LOCAL-001"


def test_cli_graph_query_traverses_relationships(monkeypatch, tmp_path, capsys) -> None:
    fixture_dir = tmp_path / "fixtures"
    fixture_dir.mkdir()
    fixture_dir.joinpath("sample.json").write_text(
        """{
  "source": {
    "source_id": "nvd_cve_2024_001",
    "source_type": "nvd",
    "title": "NVD CVE-2024-0001",
    "uri": "https://nvd.nist.gov/vuln/detail/CVE-2024-0001",
    "metadata": {}
  },
  "case": {
    "pattern_id": "LOGIC-GRAPH-TEST",
    "title": "Graph traversal test case",
    "focus": "Access Control",
    "summary": "Test case for graph relationships.",
    "source_ids": ["nvd_cve_2024_001"],
    "cwe_ids": ["CWE-639", "CWE-841"],
    "keywords": ["auth", "bypass"],
    "signals": [
      {"name": "weak_auth", "value": true, "confidence": 0.95, "description": "Weak authentication detected"}
    ],
    "workflow_steps": [],
    "evidence": [],
    "status": "validated",
    "confidence": 0.9,
    "metadata": {}
  }
}
""",
        encoding="utf-8",
    )

    monkeypatch.setenv("LOGICLLAMA_DB_PATH", str(tmp_path / "logicllama.sqlite3"))
    monkeypatch.setenv("LOGICLLAMA_FIXTURE_DIR", str(fixture_dir))

    ingest_exit = main(["ingest-fixtures"])
    assert ingest_exit == 0
    capsys.readouterr()

    # Test JSON output
    query_exit = main(["graph-query", "LOGIC-GRAPH-TEST", "--depth", "2", "--rebuild", "--format", "json"])
    output = capsys.readouterr().out
    result = json.loads(output)

    assert query_exit == 0
    assert result["query"]["start_node_id"] == "LOGIC-GRAPH-TEST"
    assert result["query"]["max_depth"] == 2
    assert len(result["nodes"]) > 0
    assert any(n["node_id"] == "LOGIC-GRAPH-TEST" for n in result["nodes"])
    assert any(n["node_id"].startswith("CWE-") for n in result["nodes"])
    assert len(result["edges"]) > 0


def test_cli_graph_query_filters_by_relation_type(monkeypatch, tmp_path, capsys) -> None:
    fixture_dir = tmp_path / "fixtures"
    fixture_dir.mkdir()
    fixture_dir.joinpath("sample.json").write_text(
        """{
  "source": {
    "source_id": "local_test_filter",
    "source_type": "local",
    "title": "Filter Test",
    "uri": "https://example.invalid/filter",
    "metadata": {}
  },
  "case": {
    "pattern_id": "LOGIC-FILTER-TEST",
    "title": "Filter test case",
    "focus": "Race Condition",
    "summary": "Test case for graph filtering.",
    "source_ids": ["local_test_filter"],
    "cwe_ids": ["CWE-362"],
    "keywords": ["race"],
    "signals": [
      {"name": "timing_signal", "value": 0.7, "confidence": 0.85, "description": "Timing variation"}
    ],
    "workflow_steps": [],
    "evidence": [],
    "status": "validated",
    "confidence": 0.75,
    "metadata": {}
  }
}
""",
        encoding="utf-8",
    )

    monkeypatch.setenv("LOGICLLAMA_DB_PATH", str(tmp_path / "logicllama.sqlite3"))
    monkeypatch.setenv("LOGICLLAMA_FIXTURE_DIR", str(fixture_dir))

    ingest_exit = main(["ingest-fixtures"])
    assert ingest_exit == 0
    capsys.readouterr()

    # Test with relation-type filter
    query_exit = main(["graph-query", "LOGIC-FILTER-TEST", "--relation-type", "maps_to", "--rebuild", "--format", "json"])
    output = capsys.readouterr().out
    result = json.loads(output)

    assert query_exit == 0
    # All edges should be maps_to relations
    assert all(e["relation"] == "maps_to" for e in result["edges"])


def test_cli_graph_query_text_output(monkeypatch, tmp_path, capsys) -> None:
    fixture_dir = tmp_path / "fixtures"
    fixture_dir.mkdir()
    fixture_dir.joinpath("sample.json").write_text(
        """{
  "source": {
    "source_id": "local_text_test",
    "source_type": "local",
    "title": "Text Test",
    "uri": "https://example.invalid/text",
    "metadata": {}
  },
  "case": {
    "pattern_id": "LOGIC-TEXT-TEST",
    "title": "Text output test",
    "focus": "Business Logic",
    "summary": "Test case for text output.",
    "source_ids": ["local_text_test"],
    "cwe_ids": [],
    "keywords": ["business"],
    "signals": [],
    "workflow_steps": [],
    "evidence": [],
    "status": "draft",
    "confidence": 0.5,
    "metadata": {}
  }
}
""",
        encoding="utf-8",
    )

    monkeypatch.setenv("LOGICLLAMA_DB_PATH", str(tmp_path / "logicllama.sqlite3"))
    monkeypatch.setenv("LOGICLLAMA_FIXTURE_DIR", str(fixture_dir))

    ingest_exit = main(["ingest-fixtures"])
    assert ingest_exit == 0
    capsys.readouterr()

    # Test text output
    query_exit = main(["graph-query", "LOGIC-TEXT-TEST", "--rebuild", "--format", "text"])
    output = capsys.readouterr().out

    assert query_exit == 0
    assert "Graph Query Results" in output
    assert "LOGIC-TEXT-TEST" in output
    assert "Nodes:" in output
    assert "Edges:" in output
