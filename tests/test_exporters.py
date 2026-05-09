"""Tests for training corpus, simulation corpus, and graph linkage exporters."""

import json
from pathlib import Path

from src.core.training_corpus import TrainingCorpusExporter
from src.core.simulation_corpus import SimulationCorpusExporter
from src.core.graph_linkage import compute_case_similarity, build_cross_case_edges, export_to_networkx
from src.core.models import LogicCase, LogicSignal, LogicStep
from src.core.cli import main


def test_training_corpus_exporter_extracts_examples() -> None:
    """Test that training corpus exporter generates Q&A pairs."""
    exporter = TrainingCorpusExporter()
    case = LogicCase(
        pattern_id="TEST-001",
        title="Test Case",
        focus="Access Control",
        summary="Test summary",
        signals=[LogicSignal(name="auth_signal", value=True, confidence=0.95, description="Auth detection")],
        workflow_steps=[
            LogicStep(step_id="s1", order=1, title="Authenticate", state_after="authenticated"),
            LogicStep(step_id="s2", order=2, title="Authorize", state_after="authorized"),
        ],
    )

    exporter.add_case(case)
    examples = exporter.corpus

    assert len(examples) > 0
    assert any(ex["type"] == "concept" for ex in examples)
    assert any(ex["type"] == "detection" for ex in examples)
    assert any(ex["type"] == "scenario" for ex in examples)
    assert any(ex["type"] == "signal" for ex in examples)


def test_training_corpus_exports_jsonl() -> None:
    """Test JSONL export format."""
    exporter = TrainingCorpusExporter()
    case = LogicCase(
        pattern_id="TEST-002",
        title="Test Case 2",
        focus="Race Condition",
        summary="Race condition summary",
    )
    exporter.add_case(case)

    jsonl = exporter.to_jsonl()
    lines = jsonl.strip().split("\n")

    assert len(lines) > 0
    for line in lines:
        obj = json.loads(line)
        assert "type" in obj
        assert "question" in obj
        assert "answer" in obj


def test_training_corpus_exports_dict() -> None:
    """Test dict export format."""
    exporter = TrainingCorpusExporter()
    case = LogicCase(
        pattern_id="TEST-003",
        title="Test Case 3",
        focus="Business Logic",
        summary="Business logic summary",
    )
    exporter.add_case(case)

    data = exporter.to_dict()
    assert data["version"] == "1.0.0"
    assert data["format"] == "training_corpus"
    assert len(data["examples"]) > 0


def test_training_corpus_statistics() -> None:
    """Test corpus statistics."""
    exporter = TrainingCorpusExporter()
    case = LogicCase(
        pattern_id="TEST-004",
        title="Test Case 4",
        focus="State Manipulation",
        summary="State manipulation summary",
        signals=[LogicSignal(name="sig1", value=1, confidence=0.8)],
    )
    exporter.add_case(case)

    stats = exporter.statistics()
    assert stats["total_examples"] > 0
    assert "by_type" in stats
    assert "by_difficulty" in stats


def test_simulation_corpus_exporter_generates_scenarios() -> None:
    """Test simulation corpus exporter generates scenarios."""
    exporter = SimulationCorpusExporter()
    case = LogicCase(
        pattern_id="SIM-001",
        title="Simulation Test",
        focus="Workflow Bypass",
        summary="Workflow bypass scenario",
        cwe_ids=["CWE-639"],
        workflow_steps=[
            LogicStep(step_id="s1", order=1, title="Step 1", state_before="s0", state_after="s1"),
            LogicStep(step_id="s2", order=2, title="Step 2", state_before="s1", state_after="s2"),
        ],
        signals=[LogicSignal(name="bypass_signal", value=True, confidence=0.9)],
    )

    exporter.add_case(case)
    simulations = exporter.simulations

    assert len(simulations) > 0
    assert any(sim["type"] == "state_transition" for sim in simulations)
    assert any(sim["type"] == "workflow_bypass" for sim in simulations)
    assert any(sim["type"] == "concurrency" for sim in simulations)
    assert any(sim["type"] == "authorization" for sim in simulations)


def test_simulation_corpus_exports_jsonl() -> None:
    """Test simulation JSONL export."""
    exporter = SimulationCorpusExporter()
    case = LogicCase(
        pattern_id="SIM-002",
        title="Simulation Test 2",
        focus="Authorization",
        summary="Authorization simulation",
        cwe_ids=["CWE-639"],
    )
    exporter.add_case(case)

    jsonl = exporter.to_jsonl()
    lines = jsonl.strip().split("\n")

    assert len(lines) > 0
    for line in lines:
        obj = json.loads(line)
        assert "type" in obj
        assert "scenario" in obj
        assert "severity" in obj


def test_simulation_corpus_statistics() -> None:
    """Test simulation corpus statistics."""
    exporter = SimulationCorpusExporter()
    case = LogicCase(
        pattern_id="SIM-003",
        title="Simulation Test 3",
        focus="Concurrency",
        summary="Concurrency simulation",
    )
    exporter.add_case(case)

    stats = exporter.statistics()
    assert stats["total_simulations"] > 0
    assert "by_type" in stats
    assert "by_severity" in stats


def test_compute_case_similarity() -> None:
    """Test case similarity computation."""
    case_a = LogicCase(
        pattern_id="A",
        title="Case A",
        focus="Access Control",
        summary="Summary A",
        cwe_ids=["CWE-639", "CWE-841"],
        keywords=["auth", "idor"],
    )

    case_b = LogicCase(
        pattern_id="B",
        title="Case B",
        focus="Access Control",
        summary="Summary B",
        cwe_ids=["CWE-639"],
        keywords=["auth", "bypass"],
    )

    case_c = LogicCase(
        pattern_id="C",
        title="Case C",
        focus="Timing",
        summary="Summary C",
        cwe_ids=["CWE-362"],
        keywords=["race", "timing"],
    )

    # Same focus + overlapping CWE + overlapping keywords
    sim_ab = compute_case_similarity(case_a, case_b)
    assert sim_ab > 0.5

    # Different focus + no overlapping CWE + no overlapping keywords
    sim_ac = compute_case_similarity(case_a, case_c)
    assert sim_ac < sim_ab

    # Perfect match
    sim_aa = compute_case_similarity(case_a, case_a)
    assert sim_aa == 1.0


def test_build_cross_case_edges() -> None:
    """Test cross-case edge generation."""
    case_a = LogicCase(
        pattern_id="X",
        title="Case X",
        focus="Access Control",
        summary="Summary X",
        cwe_ids=["CWE-639"],
        keywords=["auth"],
    )

    case_b = LogicCase(
        pattern_id="Y",
        title="Case Y",
        focus="Access Control",
        summary="Summary Y",
        cwe_ids=["CWE-639"],
        keywords=["auth"],
    )

    case_c = LogicCase(
        pattern_id="Z",
        title="Case Z",
        focus="Timing",
        summary="Summary Z",
        cwe_ids=["CWE-362"],
        keywords=["race"],
    )

    edges = build_cross_case_edges([case_a, case_b, case_c], similarity_threshold=0.3)

    # Should have edge between A and B (high similarity)
    assert any(e.from_node_id == "X" and e.to_node_id == "Y" for e in edges)

    # A-C and B-C should not have edges (low similarity)
    ac_edges = [e for e in edges if ("X" in (e.from_node_id, e.to_node_id) and "Z" in (e.from_node_id, e.to_node_id))]
    assert len(ac_edges) == 0


def test_export_to_networkx() -> None:
    """Test networkx export format."""
    from src.core.graph import GraphNode, GraphEdge, GraphNodeType, GraphRelationType

    nodes = [
        GraphNode(node_id="case1", node_type=GraphNodeType.CASE, label="Case 1"),
        GraphNode(node_id="cwe1", node_type=GraphNodeType.CWE, label="CWE-639"),
    ]

    edges = [
        GraphEdge(
            from_node_id="case1",
            to_node_id="cwe1",
            relation_type=GraphRelationType.MAPS_TO,
            weight=0.9,
        )
    ]

    output = export_to_networkx(nodes, edges)

    assert output["directed"] == True
    assert len(output["nodes"]) == 2
    assert len(output["links"]) == 1
    assert output["links"][0]["source"] == "case1"
    assert output["links"][0]["target"] == "cwe1"


def test_cli_export_training_corpus(monkeypatch, tmp_path, capsys) -> None:
    """Test CLI export-training-corpus command."""
    fixture_dir = tmp_path / "fixtures"
    fixture_dir.mkdir()
    fixture_dir.joinpath("sample.json").write_text(
        """{
  "source": {
    "source_id": "local_training",
    "source_type": "local",
    "title": "Training Source",
    "uri": "https://example.invalid/training",
    "metadata": {}
  },
  "case": {
    "pattern_id": "LOGIC-TRAINING-001",
    "title": "Training test case",
    "focus": "Access Control",
    "summary": "Test case for training export.",
    "source_ids": ["local_training"],
    "cwe_ids": ["CWE-639"],
    "keywords": ["training"],
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

    export_exit = main(["export-training-corpus", "--format", "jsonl"])
    output = capsys.readouterr().out

    lines = output.strip().split("\n")
    assert len(lines) > 0
    for line in lines:
        if line.startswith("Training corpus statistics"):
            break
        obj = json.loads(line)
        assert "type" in obj
        assert "question" in obj


def test_cli_export_simulation_corpus(monkeypatch, tmp_path, capsys) -> None:
    """Test CLI export-simulation-corpus command."""
    fixture_dir = tmp_path / "fixtures"
    fixture_dir.mkdir()
    fixture_dir.joinpath("sample.json").write_text(
        """{
  "source": {
    "source_id": "local_sim",
    "source_type": "local",
    "title": "Simulation Source",
    "uri": "https://example.invalid/sim",
    "metadata": {}
  },
  "case": {
    "pattern_id": "LOGIC-SIM-001",
    "title": "Simulation test case",
    "focus": "Workflow Bypass",
    "summary": "Test case for simulation export.",
    "source_ids": ["local_sim"],
    "cwe_ids": ["CWE-841"],
    "keywords": ["workflow"],
    "signals": [],
    "workflow_steps": [],
    "evidence": [],
    "status": "validated",
    "confidence": 0.85,
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

    export_exit = main(["export-simulation-corpus", "--format", "jsonl"])
    output = capsys.readouterr().out

    lines = output.strip().split("\n")
    assert len(lines) > 0
    for line in lines:
        if line.startswith("Simulation corpus"):
            break
        obj = json.loads(line)
        assert "type" in obj
        assert "scenario" in obj
