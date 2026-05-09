"""SQLite persistence for normalized LogicLlama records."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from datetime import datetime, timezone
from typing import Any

from .models import LogicCase, LogicSource, QueryFilter
from .graph import GraphNode, GraphEdge, GraphNodeType, GraphRelationType, GraphQueryEngine, GraphQuery, GraphTraversalResult


class SQLiteLogicStore:
    """Thin SQLite adapter for the first LogicLlama milestone."""

    def __init__(self, database_path: Path) -> None:
        self.database_path = Path(database_path)

    def connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.database_path)
        connection.row_factory = sqlite3.Row
        # Enforce foreign key constraints for graph relationships and referential integrity
        try:
            connection.execute("PRAGMA foreign_keys = ON")
        except Exception:
            # Best-effort: some pysqlite wrappers may restrict PRAGMA execution timing
            pass
        return connection

    def initialize(self) -> None:
        with self.connect() as connection:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS sources (
                    source_id TEXT PRIMARY KEY,
                    source_type TEXT NOT NULL,
                    title TEXT NOT NULL,
                    uri TEXT NOT NULL,
                    retrieved_at TEXT NOT NULL,
                    license TEXT,
                    metadata_json TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS cases (
                    pattern_id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    focus TEXT NOT NULL,
                    summary TEXT NOT NULL,
                    source_type TEXT NOT NULL,
                    source_ids_json TEXT NOT NULL,
                    cwe_ids_json TEXT NOT NULL,
                    keywords_json TEXT NOT NULL,
                    signals_json TEXT NOT NULL,
                    workflow_steps_json TEXT NOT NULL,
                    evidence_json TEXT NOT NULL,
                    status TEXT NOT NULL,
                    confidence REAL NOT NULL,
                    metadata_json TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS sync_runs (
                    run_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    source_name TEXT NOT NULL,
                    records_fetched INTEGER NOT NULL,
                    records_ingested INTEGER NOT NULL,
                    status TEXT NOT NULL,
                    started_at TEXT NOT NULL,
                    finished_at TEXT NOT NULL,
                    metadata_json TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS graph_nodes (
                    node_id TEXT PRIMARY KEY,
                    node_type TEXT NOT NULL,
                    label TEXT NOT NULL,
                    description TEXT,
                    metadata_json TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS graph_edges (
                    edge_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    from_node_id TEXT NOT NULL,
                    to_node_id TEXT NOT NULL,
                    relation_type TEXT NOT NULL,
                    weight REAL,
                    metadata_json TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (from_node_id) REFERENCES graph_nodes(node_id),
                    FOREIGN KEY (to_node_id) REFERENCES graph_nodes(node_id),
                    UNIQUE(from_node_id, to_node_id, relation_type)
                );

                CREATE INDEX IF NOT EXISTS idx_graph_edges_from ON graph_edges(from_node_id);
                CREATE INDEX IF NOT EXISTS idx_graph_edges_to ON graph_edges(to_node_id);
                CREATE INDEX IF NOT EXISTS idx_graph_edges_relation ON graph_edges(relation_type);
                CREATE INDEX IF NOT EXISTS idx_graph_nodes_type ON graph_nodes(node_type);
                """
            )

    def upsert_source(self, source: LogicSource) -> None:
        payload = source.model_dump(mode="json")
        with self.connect() as connection:
            connection.execute(
                """
                INSERT INTO sources (
                    source_id, source_type, title, uri, retrieved_at, license, metadata_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(source_id) DO UPDATE SET
                    source_type=excluded.source_type,
                    title=excluded.title,
                    uri=excluded.uri,
                    retrieved_at=excluded.retrieved_at,
                    license=excluded.license,
                    metadata_json=excluded.metadata_json
                """,
                (
                    payload["source_id"],
                    payload["source_type"],
                    payload["title"],
                    payload["uri"],
                    payload["retrieved_at"],
                    payload["license"],
                    json.dumps(payload["metadata"], ensure_ascii=True),
                ),
            )

    def upsert_case(self, logic_case: LogicCase) -> None:
        payload = logic_case.model_dump(mode="json")
        with self.connect() as connection:
            connection.execute(
                """
                INSERT INTO cases (
                    pattern_id, title, focus, summary, source_type, source_ids_json, cwe_ids_json,
                    keywords_json, signals_json, workflow_steps_json, evidence_json,
                    status, confidence, metadata_json, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(pattern_id) DO UPDATE SET
                    title=excluded.title,
                    focus=excluded.focus,
                    summary=excluded.summary,
                    source_type=excluded.source_type,
                    source_ids_json=excluded.source_ids_json,
                    cwe_ids_json=excluded.cwe_ids_json,
                    keywords_json=excluded.keywords_json,
                    signals_json=excluded.signals_json,
                    workflow_steps_json=excluded.workflow_steps_json,
                    evidence_json=excluded.evidence_json,
                    status=excluded.status,
                    confidence=excluded.confidence,
                    metadata_json=excluded.metadata_json,
                    created_at=excluded.created_at,
                    updated_at=excluded.updated_at
                """,
                (
                    payload["pattern_id"],
                    payload["title"],
                    payload["focus"],
                    payload["summary"],
                    payload["source_type"],
                    json.dumps(payload["source_ids"], ensure_ascii=True),
                    json.dumps(payload["cwe_ids"], ensure_ascii=True),
                    json.dumps(payload["keywords"], ensure_ascii=True),
                    json.dumps(payload["signals"], ensure_ascii=True),
                    json.dumps(payload["workflow_steps"], ensure_ascii=True),
                    json.dumps(payload["evidence"], ensure_ascii=True),
                    payload["status"],
                    payload["confidence"],
                    json.dumps(payload["metadata"], ensure_ascii=True),
                    payload["created_at"],
                    payload["updated_at"],
                ),
            )

    def list_cases(self, limit: int = 100) -> list[LogicCase]:
        with self.connect() as connection:
            rows = connection.execute(
                """
                SELECT *
                FROM cases
                ORDER BY updated_at DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()
        return [self._row_to_case(row) for row in rows]

    def get_case(self, pattern_id: str) -> LogicCase | None:
        with self.connect() as connection:
            row = connection.execute(
                "SELECT * FROM cases WHERE pattern_id = ?",
                (pattern_id,),
            ).fetchone()
        if row is None:
            return None
        return self._row_to_case(row)

    def list_sources(self, limit: int = 100) -> list[LogicSource]:
        with self.connect() as connection:
            rows = connection.execute(
                """
                SELECT *
                FROM sources
                ORDER BY retrieved_at DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()
        return [self._row_to_source(row) for row in rows]

    def get_source(self, source_id: str) -> LogicSource | None:
        with self.connect() as connection:
            row = connection.execute(
                "SELECT * FROM sources WHERE source_id = ?",
                (source_id,),
            ).fetchone()
        if row is None:
            return None
        return self._row_to_source(row)

    def count_cases(self) -> int:
        with self.connect() as connection:
            row = connection.execute("SELECT COUNT(*) AS count FROM cases").fetchone()
        return int(row["count"] if row is not None else 0)

    def count_sources(self) -> int:
        with self.connect() as connection:
            row = connection.execute("SELECT COUNT(*) AS count FROM sources").fetchone()
        return int(row["count"] if row is not None else 0)

    def count_cases_by_source_type(self) -> dict[str, int]:
        with self.connect() as connection:
            rows = connection.execute(
                """
                SELECT source_type, COUNT(*) AS count
                FROM cases
                GROUP BY source_type
                ORDER BY source_type
                """
            ).fetchall()
        return {str(row["source_type"]): int(row["count"]) for row in rows}

    def count_sources_by_source_type(self) -> dict[str, int]:
        with self.connect() as connection:
            rows = connection.execute(
                """
                SELECT source_type, COUNT(*) AS count
                FROM sources
                GROUP BY source_type
                ORDER BY source_type
                """
            ).fetchall()
        return {str(row["source_type"]): int(row["count"]) for row in rows}

    def record_sync_run(
        self,
        source_name: str,
        records_fetched: int,
        records_ingested: int,
        status: str = "success",
        metadata: dict[str, Any] | None = None,
    ) -> None:
        payload = json.dumps(metadata or {}, ensure_ascii=True)
        timestamp = datetime.now(timezone.utc).isoformat()
        with self.connect() as connection:
            connection.execute(
                """
                INSERT INTO sync_runs (
                    source_name, records_fetched, records_ingested, status, started_at, finished_at, metadata_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (source_name, records_fetched, records_ingested, status, timestamp, timestamp, payload),
            )

    def list_sync_runs(self, limit: int = 20) -> list[dict[str, Any]]:
        with self.connect() as connection:
            rows = connection.execute(
                """
                SELECT *
                FROM sync_runs
                ORDER BY run_id DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()
        return [self._row_to_sync_run(row) for row in rows]

    def search_cases(self, query: QueryFilter) -> list[LogicCase]:
        candidates = self.list_cases(limit=500)
        tokens: list[str] = []
        if query.text:
            tokens.extend(query.text.lower().split())
        if query.keyword:
            tokens.append(query.keyword.lower())
        if query.cwe_id:
            tokens.append(query.cwe_id.lower())

        filtered: list[LogicCase] = []
        for logic_case in candidates:
            if query.source_type is not None and logic_case.source_type != query.source_type:
                continue

            haystack = " ".join(
                [
                    logic_case.pattern_id,
                    logic_case.title,
                    logic_case.focus,
                    logic_case.summary,
                    " ".join(logic_case.keywords),
                    " ".join(logic_case.cwe_ids),
                ]
            ).lower()
            if tokens and not all(token in haystack for token in tokens):
                continue
            filtered.append(logic_case)

        return filtered[: query.limit]

    def _row_to_case(self, row: sqlite3.Row) -> LogicCase:
        return LogicCase(
            pattern_id=row["pattern_id"],
            title=row["title"],
            focus=row["focus"],
            summary=row["summary"],
            source_type=row["source_type"],
            source_ids=self._load_json_array(row["source_ids_json"]),
            cwe_ids=self._load_json_array(row["cwe_ids_json"]),
            keywords=self._load_json_array(row["keywords_json"]),
            signals=self._load_json(row["signals_json"]),
            workflow_steps=self._load_json(row["workflow_steps_json"]),
            evidence=self._load_json(row["evidence_json"]),
            status=row["status"],
            confidence=row["confidence"],
            metadata=self._load_json(row["metadata_json"]),
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )

    def _row_to_source(self, row: sqlite3.Row) -> LogicSource:
        return LogicSource(
            source_id=row["source_id"],
            source_type=row["source_type"],
            title=row["title"],
            uri=row["uri"],
            retrieved_at=row["retrieved_at"],
            license=row["license"],
            metadata=self._load_json(row["metadata_json"]),
        )

    @staticmethod
    def _load_json(value: str):
        return json.loads(value)

    @staticmethod
    def _load_json_array(value: str) -> list[str]:
        loaded = json.loads(value)
        return [str(item) for item in loaded]

    @staticmethod
    def _row_to_sync_run(row: sqlite3.Row) -> dict[str, Any]:
        return {
            "run_id": int(row["run_id"]),
            "source_name": str(row["source_name"]),
            "records_fetched": int(row["records_fetched"]),
            "records_ingested": int(row["records_ingested"]),
            "status": str(row["status"]),
            "started_at": str(row["started_at"]),
            "finished_at": str(row["finished_at"]),
            "metadata": json.loads(row["metadata_json"]),
        }

    def upsert_graph_node(self, node: GraphNode) -> None:
        """Insert or update a graph node."""
        timestamp = datetime.now(timezone.utc).isoformat()
        with self.connect() as connection:
            connection.execute(
                """
                INSERT INTO graph_nodes (
                    node_id, node_type, label, description, metadata_json, created_at
                ) VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(node_id) DO UPDATE SET
                    node_type=excluded.node_type,
                    label=excluded.label,
                    description=excluded.description,
                    metadata_json=excluded.metadata_json
                """,
                (
                    node.node_id,
                    node.node_type.value,
                    node.label,
                    node.description,
                    json.dumps(node.metadata or {}, ensure_ascii=True),
                    timestamp,
                ),
            )

    def upsert_graph_edge(self, edge: GraphEdge) -> None:
        """Insert or update a graph edge."""
        timestamp = datetime.now(timezone.utc).isoformat()
        with self.connect() as connection:
            # First ensure both nodes exist
            connection.execute(
                "INSERT OR IGNORE INTO graph_nodes (node_id, node_type, label, metadata_json, created_at) VALUES (?, ?, ?, ?, ?)",
                (edge.from_node_id, "case", edge.from_node_id, "{}", timestamp),
            )
            connection.execute(
                "INSERT OR IGNORE INTO graph_nodes (node_id, node_type, label, metadata_json, created_at) VALUES (?, ?, ?, ?, ?)",
                (edge.to_node_id, "case", edge.to_node_id, "{}", timestamp),
            )
            # Then insert/update the edge
            connection.execute(
                """
                INSERT INTO graph_edges (
                    from_node_id, to_node_id, relation_type, weight, metadata_json, created_at
                ) VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(from_node_id, to_node_id, relation_type) DO UPDATE SET
                    weight=excluded.weight,
                    metadata_json=excluded.metadata_json
                """,
                (
                    edge.from_node_id,
                    edge.to_node_id,
                    edge.relation_type.value,
                    edge.weight,
                    json.dumps(edge.metadata or {}, ensure_ascii=True),
                    timestamp,
                ),
            )

    def load_graph_for_case(self, pattern_id: str) -> tuple[list[GraphNode], list[GraphEdge]]:
        """Load all graph nodes and edges related to a case."""
        with self.connect() as connection:
            # Load nodes
            node_rows = connection.execute(
                """
                SELECT DISTINCT gn.* FROM graph_nodes gn
                WHERE gn.node_id IN (
                    SELECT from_node_id FROM graph_edges WHERE from_node_id = ? OR to_node_id = ?
                    UNION
                    SELECT to_node_id FROM graph_edges WHERE from_node_id = ? OR to_node_id = ?
                    UNION
                    SELECT ? as node_id
                )
                """,
                (pattern_id, pattern_id, pattern_id, pattern_id, pattern_id),
            ).fetchall()

            # Load edges
            edge_rows = connection.execute(
                """
                SELECT * FROM graph_edges
                WHERE from_node_id IN (
                    SELECT node_id FROM graph_nodes
                ) AND to_node_id IN (
                    SELECT node_id FROM graph_nodes
                )
                """,
            ).fetchall()

        nodes = [self._row_to_graph_node(row) for row in node_rows]
        edges = [self._row_to_graph_edge(row) for row in edge_rows]
        return nodes, edges

    def query_graph(self, query: GraphQuery) -> GraphTraversalResult:
        """Execute a graph traversal query."""
        nodes, edges = self.load_graph_for_case(query.start_node_id)
        engine = GraphQueryEngine(nodes, edges)
        return engine.traverse(query)

    def get_case_neighbors(self, pattern_id: str, relation_types: list[GraphRelationType] | None = None) -> list[GraphNode]:
        """Get immediate neighbors of a case in the graph."""
        nodes, edges = self.load_graph_for_case(pattern_id)
        engine = GraphQueryEngine(nodes, edges)
        return engine.neighbors(pattern_id, relation_types)

    def count_graph_nodes(self) -> int:
        """Count nodes in the graph."""
        with self.connect() as connection:
            row = connection.execute("SELECT COUNT(*) AS count FROM graph_nodes").fetchone()
        return int(row["count"] if row is not None else 0)

    def count_graph_edges(self) -> int:
        """Count edges in the graph."""
        with self.connect() as connection:
            row = connection.execute("SELECT COUNT(*) AS count FROM graph_edges").fetchone()
        return int(row["count"] if row is not None else 0)

    @staticmethod
    def _row_to_graph_node(row: sqlite3.Row) -> GraphNode:
        return GraphNode(
            node_id=row["node_id"],
            node_type=GraphNodeType(row["node_type"]),
            label=row["label"],
            description=row["description"],
            metadata=json.loads(row["metadata_json"]),
        )

    @staticmethod
    def _row_to_graph_edge(row: sqlite3.Row) -> GraphEdge:
        return GraphEdge(
            from_node_id=row["from_node_id"],
            to_node_id=row["to_node_id"],
            relation_type=GraphRelationType(row["relation_type"]),
            weight=row["weight"],
            metadata=json.loads(row["metadata_json"]),
        )
