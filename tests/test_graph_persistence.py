"""Tests for Neo4j graph persistence layer."""

from __future__ import annotations

import pytest
from datetime import datetime, timezone
from unittest.mock import Mock, MagicMock, patch

from src.core.models import LogicCase, LogicSourceType
from src.core.graph_persistence import Neo4jGraphStore
from src.core.graph import GraphEdge, GraphRelationType


@pytest.fixture
def sample_cases():
    """Create sample cases for testing."""
    case_a = LogicCase(
        pattern_id="PAT-001",
        title="SQL Injection in Login Form",
        summary="SQL injection vulnerability in authentication endpoint",
        focus="sql_injection",
        source_type=LogicSourceType.NVD,
        source_ids=["CVE-2025-0001"],
        cwe_ids=["89"],
        keywords=["sql", "injection", "authentication"],
        metadata={"severity": "high"},
        created_at=datetime.now(timezone.utc),
    )

    case_b = LogicCase(
        pattern_id="PAT-002",
        title="SQL Injection in Search",
        summary="SQL injection vulnerability in search functionality",
        focus="sql_injection",
        source_type=LogicSourceType.NVD,
        source_ids=["CVE-2025-0002"],
        cwe_ids=["89"],
        keywords=["sql", "injection", "search"],
        metadata={"severity": "high"},
        created_at=datetime.now(timezone.utc),
    )

    case_c = LogicCase(
        pattern_id="PAT-003",
        title="Cross-Site Scripting in Comments",
        summary="XSS vulnerability in user comments section",
        focus="xss",
        source_type=LogicSourceType.KEV,
        source_ids=["CVE-2025-0003"],
        cwe_ids=["79"],
        keywords=["xss", "cross-site", "scripting"],
        metadata={"severity": "medium"},
        created_at=datetime.now(timezone.utc),
    )

    return [case_a, case_b, case_c]


class TestNeo4jGraphStoreInitialization:
    """Test Neo4j connection and schema initialization."""

    def test_neo4j_store_initialization(self):
        """Verify Neo4jGraphStore can be instantiated."""
        store = Neo4jGraphStore(
            uri="bolt://localhost:7687",
            username="neo4j",
            password="password",
        )
        assert store.uri == "bolt://localhost:7687"
        assert store.username == "neo4j"
        assert store.password == "password"

    def test_neo4j_store_custom_database(self):
        """Verify custom database name."""
        store = Neo4jGraphStore(
            uri="bolt://localhost:7687",
            database="logicllama_test",
        )
        assert store.database == "logicllama_test"

    def test_connect_raises_without_service(self):
        """Verify connect() raises error when Neo4j is unavailable."""
        store = Neo4jGraphStore(
            uri="bolt://invalid-host:7687",
            username="neo4j",
            password="password",
        )
        with pytest.raises(Exception):
            store.connect()

    def test_disconnect_safe_when_not_connected(self):
        """Verify disconnect() is safe without connection."""
        store = Neo4jGraphStore()
        store.disconnect()  # Should not raise


class TestNeo4jGraphStoreMocking:
    """Test graph persistence operations with mocked Neo4j."""

    @patch("src.core.graph_persistence.GraphDatabase.driver")
    def test_sync_case_node(self, mock_driver_class, sample_cases):
        """Verify sync_case_node creates correct Cypher query."""
        # Setup mock driver
        mock_driver = MagicMock()
        mock_session = MagicMock()
        mock_driver.session.return_value.__enter__.return_value = mock_session
        mock_driver_class.return_value = mock_driver

        store = Neo4jGraphStore()
        store._driver = mock_driver

        case = sample_cases[0]
        store.sync_case_node(case)

        # Verify session was used
        mock_driver.session.assert_called()
        mock_session.run.assert_called()

    @patch("src.core.graph_persistence.GraphDatabase.driver")
    def test_sync_cwe_nodes(self, mock_driver_class, sample_cases):
        """Verify sync_cwe_nodes creates CWE relationships."""
        mock_driver = MagicMock()
        mock_session = MagicMock()
        mock_driver.session.return_value.__enter__.return_value = mock_session
        mock_driver_class.return_value = mock_driver

        store = Neo4jGraphStore()
        store._driver = mock_driver

        case = sample_cases[0]  # Has CWE-89
        store.sync_cwe_nodes(case)

        # Should have created MAPS_TO relationship for each CWE
        assert mock_session.run.call_count >= len(case.cwe_ids)

    @patch("src.core.graph_persistence.GraphDatabase.driver")
    def test_sync_cross_case_edges(self, mock_driver_class, sample_cases):
        """Verify sync_cross_case_edges processes edge list."""
        mock_driver = MagicMock()
        mock_session = MagicMock()
        mock_driver.session.return_value.__enter__.return_value = mock_session
        mock_driver_class.return_value = mock_driver

        store = Neo4jGraphStore()
        store._driver = mock_driver

        # Create sample edges
        edges = [
            GraphEdge(
                from_node_id="PAT-001",
                to_node_id="PAT-002",
                relation_type=GraphRelationType.VARIANT_OF,
                weight=0.85,
                metadata={"similarity": 0.85},
            )
        ]

        store.sync_cross_case_edges(edges)

        # Verify session run was called
        assert mock_session.run.call_count >= 1

    @patch("src.core.graph_linkage.build_cross_case_edges")
    @patch("src.core.graph_persistence.GraphDatabase.driver")
    def test_sync_all_cases(self, mock_driver_class, mock_build_edges, sample_cases):
        """Verify sync_all_cases orchestrates full sync."""
        mock_driver = MagicMock()
        mock_session = MagicMock()
        mock_driver.session.return_value.__enter__.return_value = mock_session
        mock_driver_class.return_value = mock_driver
        mock_build_edges.return_value = []

        store = Neo4jGraphStore()
        store._driver = mock_driver

        result = store.sync_all_cases(sample_cases)

        assert result["cases_synced"] == 3
        assert result["edges_created"] == 0
        assert "timestamp" in result

    @patch("src.core.graph_persistence.GraphDatabase.driver")
    def test_query_similar_cases(self, mock_driver_class):
        """Verify query_similar_cases returns results."""
        mock_driver = MagicMock()
        mock_session = MagicMock()

        # Mock query result
        mock_record = Mock()
        mock_record.__getitem__ = lambda self, key: {
            "pattern_id": "PAT-002",
            "title": "Similar Case",
            "focus": "sql_injection",
            "similarity": 0.85,
            "relation_type": "VARIANT_OF",
        }.get(key)
        mock_record.keys.return_value = ["pattern_id", "title", "focus", "similarity", "relation_type"]

        mock_result = MagicMock()
        mock_result.__iter__ = lambda self: iter([mock_record])
        mock_session.run.return_value = mock_result
        mock_driver.session.return_value.__enter__.return_value = mock_session
        mock_driver_class.return_value = mock_driver

        store = Neo4jGraphStore()
        store._driver = mock_driver

        results = store.query_similar_cases("PAT-001", limit=10)

        assert len(results) >= 1
        mock_session.run.assert_called()

    @patch("src.core.graph_persistence.GraphDatabase.driver")
    def test_query_cwe_cases(self, mock_driver_class):
        """Verify query_cwe_cases finds CWE-mapped cases."""
        mock_driver = MagicMock()
        mock_session = MagicMock()

        # Create a proper mock record that behaves like dict access
        mock_record = {
            "pattern_id": "PAT-001",
            "title": "SQL Injection Case",
            "focus": "sql_injection",
            "source_type": "nvd",
        }

        mock_result = MagicMock()
        mock_result.__iter__ = lambda self: iter([mock_record])
        mock_session.run.return_value = mock_result
        mock_driver.session.return_value.__enter__.return_value = mock_session
        mock_driver_class.return_value = mock_driver

        store = Neo4jGraphStore()
        store._driver = mock_driver

        results = store.query_cwe_cases("89", limit=10)

        assert len(results) >= 1

    @patch("src.core.graph_persistence.GraphDatabase.driver")
    def test_query_focus_cluster(self, mock_driver_class):
        """Verify query_focus_cluster groups by focus."""
        mock_driver = MagicMock()
        mock_session = MagicMock()

        mock_result = MagicMock()
        mock_result.__iter__ = lambda self: iter([])
        mock_session.run.return_value = mock_result
        mock_driver.session.return_value.__enter__.return_value = mock_session
        mock_driver_class.return_value = mock_driver

        store = Neo4jGraphStore()
        store._driver = mock_driver

        results = store.query_focus_cluster("sql_injection", limit=10)

        # Should return list (even if empty in this mock)
        assert isinstance(results, list)

    @patch("src.core.graph_persistence.GraphDatabase.driver")
    def test_get_graph_stats(self, mock_driver_class):
        """Verify get_graph_stats collects graph metrics."""
        mock_driver = MagicMock()
        mock_session = MagicMock()

        # Mock responses for different stat queries
        def mock_run(query, **kwargs):
            result = MagicMock()
            if "Case" in query and "COUNT" in query:
                record = Mock()
                record.__getitem__ = lambda self, key: {"count": 100}.get(key)
                result.single.return_value = record
            elif "CWE" in query and "COUNT" in query:
                record = Mock()
                record.__getitem__ = lambda self, key: {"count": 950}.get(key)
                result.single.return_value = record
            elif "RELATED_TO" in query:
                record = Mock()
                record.__getitem__ = lambda self, key: {"count": 500}.get(key)
                result.single.return_value = record
            elif "avg_weight" in query:
                record = Mock()
                record.__getitem__ = lambda self, key: {"avg_weight": 0.65}.get(key)
                result.single.return_value = record
            else:
                result.single.return_value = None
            return result

        mock_session.run.side_effect = mock_run
        mock_driver.session.return_value.__enter__.return_value = mock_session
        mock_driver_class.return_value = mock_driver

        store = Neo4jGraphStore()
        store._driver = mock_driver

        stats = store.get_graph_stats()

        assert "nodes_by_type" in stats
        assert "edges_by_type" in stats
        assert "total_nodes" in stats
        assert "total_edges" in stats
        assert "timestamp" in stats

    def test_neo4j_store_without_driver_raises(self):
        """Verify operations fail gracefully without driver."""
        store = Neo4jGraphStore()

        with pytest.raises(RuntimeError):
            store.sync_case_node(Mock())

        with pytest.raises(RuntimeError):
            store.query_similar_cases("PAT-001")

        with pytest.raises(RuntimeError):
            store.get_graph_stats()
