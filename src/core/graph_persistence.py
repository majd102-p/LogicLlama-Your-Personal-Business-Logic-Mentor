"""Neo4j graph persistence layer for knowledge graph storage and querying."""

from __future__ import annotations

import json
import logging
from typing import Any, Optional
from datetime import datetime, timezone

from neo4j import Driver, GraphDatabase, basic_auth
from neo4j.exceptions import Neo4jError

from .models import LogicCase
from .graph import GraphNode, GraphEdge, GraphNodeType, GraphRelationType


logger = logging.getLogger(__name__)


class Neo4jGraphStore:
    """Neo4j-backed graph persistence with node/edge sync from SQLite."""

    def __init__(
        self,
        uri: str = "bolt://localhost:7687",
        username: str = "neo4j",
        password: str = "password",
        database: str = "neo4j",
        verify_ssl: bool = True,
    ):
        """Initialize Neo4j connection."""
        self.uri = uri
        self.username = username
        self.password = password
        self.database = database
        self.verify_ssl = verify_ssl
        self._driver: Optional[Driver] = None

    def connect(self) -> None:
        """Establish Neo4j connection."""
        try:
            self._driver = GraphDatabase.driver(
                self.uri,
                auth=basic_auth(self.username, self.password),
                encrypted=self.verify_ssl,
            )
            # Verify connection
            with self._driver.session(database=self.database) as session:
                session.run("RETURN 1")
            logger.info(f"Connected to Neo4j at {self.uri}")
        except Neo4jError as e:
            logger.error(f"Failed to connect to Neo4j: {e}")
            raise

    def disconnect(self) -> None:
        """Close Neo4j connection."""
        if self._driver:
            self._driver.close()
            logger.info("Disconnected from Neo4j")

    def initialize_schema(self) -> None:
        """Create indexes and constraints for optimal query performance."""
        if not self._driver:
            raise RuntimeError("Neo4j driver not initialized. Call connect() first.")

        constraints_and_indexes = [
            # Constraints
            "CREATE CONSTRAINT IF NOT EXISTS FOR (n:Case) REQUIRE n.pattern_id IS UNIQUE",
            "CREATE CONSTRAINT IF NOT EXISTS FOR (n:CWE) REQUIRE n.cwe_id IS UNIQUE",
            "CREATE CONSTRAINT IF NOT EXISTS FOR (n:Source) REQUIRE n.source_id IS UNIQUE",
            # Indexes for performance
            "CREATE INDEX IF NOT EXISTS FOR (n:Case) ON (n.focus)",
            "CREATE INDEX IF NOT EXISTS FOR (n:Case) ON (n.source_type)",
            "CREATE INDEX IF NOT EXISTS FOR (n:Case) ON (n.created_at)",
            "CREATE INDEX IF NOT EXISTS FOR (n:CWE) ON (n.cwe_type)",
            "CREATE INDEX IF NOT EXISTS FOR (r:RELATED_TO) ON (r.weight)",
            "CREATE INDEX IF NOT EXISTS FOR (r:VARIANT_OF) ON (r.weight)",
        ]

        with self._driver.session(database=self.database) as session:
            for constraint_or_index in constraints_and_indexes:
                try:
                    session.run(constraint_or_index)
                    logger.debug(f"Executed: {constraint_or_index[:50]}...")
                except Neo4jError as e:
                    logger.debug(f"Constraint/index already exists: {e}")

    def sync_case_node(self, case: LogicCase) -> None:
        """Upsert a single case as a graph node."""
        if not self._driver:
            raise RuntimeError("Neo4j driver not initialized. Call connect() first.")

        cypher = """
        MERGE (c:Case {pattern_id: $pattern_id})
        SET c.title = $title,
            c.focus = $focus,
            c.source_type = $source_type,
            c.keywords = $keywords,
            c.metadata = $metadata,
            c.created_at = datetime($created_at),
            c.updated_at = datetime($updated_at)
        RETURN c.pattern_id
        """

        params = {
            "pattern_id": case.pattern_id,
            "title": case.title,
            "focus": case.focus,
            "source_type": case.source_type.value,
            "keywords": case.keywords,
            "metadata": json.dumps(case.metadata),
            "created_at": case.created_at.isoformat() if case.created_at else datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }

        with self._driver.session(database=self.database) as session:
            result = session.run(cypher, params)
            result.consume()

    def sync_cwe_nodes(self, case: LogicCase) -> None:
        """Create or link CWE nodes for a case."""
        if not self._driver:
            raise RuntimeError("Neo4j driver not initialized. Call connect() first.")

        cypher = """
        MERGE (cwe:CWE {cwe_id: $cwe_id})
        SET cwe.cwe_type = 'weakness'
        WITH cwe
        MATCH (c:Case {pattern_id: $pattern_id})
        MERGE (c)-[:MAPS_TO]->(cwe)
        """

        with self._driver.session(database=self.database) as session:
            for cwe_id in case.cwe_ids:
                params = {"cwe_id": cwe_id, "pattern_id": case.pattern_id}
                session.run(cypher, params)

    def sync_cross_case_edges(self, edges: list[GraphEdge]) -> None:
        """Sync cross-case similarity edges from SQLite."""
        if not self._driver:
            raise RuntimeError("Neo4j driver not initialized. Call connect() first.")

        with self._driver.session(database=self.database) as session:
            for edge in edges:
                relation_type = edge.relation_type.value.upper()
                cypher = f"""
                MATCH (c1:Case {{pattern_id: $from_node_id}})
                MATCH (c2:Case {{pattern_id: $to_node_id}})
                MERGE (c1)-[r:{relation_type} {{weight: $weight}}]->(c2)
                SET r.metadata = $metadata,
                    r.created_at = datetime($created_at)
                RETURN r
                """
                params = {
                    "from_node_id": edge.from_node_id,
                    "to_node_id": edge.to_node_id,
                    "weight": edge.weight,
                    "metadata": json.dumps(edge.metadata),
                    "created_at": datetime.now(timezone.utc).isoformat(),
                }
                session.run(cypher, params)

    def sync_all_cases(self, cases: list[LogicCase]) -> dict[str, Any]:
        """Batch sync all cases and build cross-case relationships."""
        if not self._driver:
            raise RuntimeError("Neo4j driver not initialized. Call connect() first.")

        logger.info(f"Syncing {len(cases)} cases to Neo4j...")

        # Clear existing graph (optional)
        with self._driver.session(database=self.database) as session:
            session.run("MATCH (n) DETACH DELETE n")
            logger.debug("Cleared existing Neo4j graph")

        # Initialize schema
        self.initialize_schema()

        # Sync all case nodes
        for i, case in enumerate(cases):
            self.sync_case_node(case)
            self.sync_cwe_nodes(case)
            if (i + 1) % 1000 == 0:
                logger.info(f"  Synced {i + 1}/{len(cases)} cases")

        logger.info(f"Successfully synced {len(cases)} case nodes to Neo4j")

        # Build and sync cross-case relationships
        from .graph_linkage import build_cross_case_edges

        edges = build_cross_case_edges(cases, similarity_threshold=0.3)
        logger.info(f"Building {len(edges)} cross-case edges...")

        self.sync_cross_case_edges(edges)
        logger.info(f"Successfully synced {len(edges)} cross-case edges to Neo4j")

        return {
            "cases_synced": len(cases),
            "edges_created": len(edges),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    def query_similar_cases(self, pattern_id: str, limit: int = 10) -> list[dict[str, Any]]:
        """Find similar cases using graph relationships."""
        if not self._driver:
            raise RuntimeError("Neo4j driver not initialized. Call connect() first.")

        cypher = """
        MATCH (c1:Case {pattern_id: $pattern_id})-[r:RELATED_TO|VARIANT_OF]-(c2:Case)
        RETURN c2.pattern_id AS pattern_id,
               c2.title AS title,
               c2.focus AS focus,
               r.weight AS similarity,
               type(r) AS relation_type
        ORDER BY r.weight DESC
        LIMIT $limit
        """

        params = {"pattern_id": pattern_id, "limit": limit}

        with self._driver.session(database=self.database) as session:
            result = session.run(cypher, params)
            return [dict(record) for record in result]

    def query_cwe_cases(self, cwe_id: str, limit: int = 10) -> list[dict[str, Any]]:
        """Find all cases mapping to a specific CWE."""
        cypher = """
        MATCH (c:Case)-[:MAPS_TO]->(cwe:CWE {cwe_id: $cwe_id})
        RETURN c.pattern_id AS pattern_id,
               c.title AS title,
               c.focus AS focus,
               c.source_type AS source_type
        LIMIT $limit
        """

        params = {"cwe_id": cwe_id, "limit": limit}

        with self._driver.session(database=self.database) as session:
            result = session.run(cypher, params)
            return [dict(record) for record in result]

    def query_focus_cluster(self, focus: str, limit: int = 10) -> list[dict[str, Any]]:
        """Find all cases with a specific focus."""
        cypher = """
        MATCH (c:Case {focus: $focus})
        RETURN c.pattern_id AS pattern_id,
               c.title AS title,
               c.source_type AS source_type
        LIMIT $limit
        """

        params = {"focus": focus, "limit": limit}

        with self._driver.session(database=self.database) as session:
            result = session.run(cypher, params)
            return [dict(record) for record in result]

    def get_graph_stats(self) -> dict[str, Any]:
        """Get graph statistics."""
        if not self._driver:
            raise RuntimeError("Neo4j driver not initialized. Call connect() first.")

        with self._driver.session(database=self.database) as session:
            # Count nodes by type
            nodes_by_type = {}
            for node_type in ["Case", "CWE", "Source"]:
                result = session.run(f"MATCH (n:{node_type}) RETURN COUNT(n) AS count")
                record = result.single()
                if record:
                    nodes_by_type[node_type] = record["count"]

            # Count edges by type
            edges_by_type = {}
            for edge_type in ["RELATED_TO", "VARIANT_OF", "MAPS_TO"]:
                result = session.run(f"MATCH ()-[r:{edge_type}]-() RETURN COUNT(r) AS count")
                record = result.single()
                if record:
                    edges_by_type[edge_type] = record["count"]

            # Average similarity
            avg_similarity = None
            result = session.run("MATCH ()-[r:RELATED_TO|VARIANT_OF]->() RETURN AVG(r.weight) AS avg_weight")
            record = result.single()
            if record and record["avg_weight"] is not None:
                avg_similarity = round(record["avg_weight"], 3)

            return {
                "nodes_by_type": nodes_by_type,
                "edges_by_type": edges_by_type,
                "avg_similarity": avg_similarity,
                "total_nodes": sum(nodes_by_type.values()),
                "total_edges": sum(edges_by_type.values()),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }

    def export_for_analytics(self, output_path: str) -> None:
        """Export graph in GraphML format for network analysis."""
        if not self._driver:
            raise RuntimeError("Neo4j driver not initialized. Call connect() first.")

        # Export as JSON (alternative to GraphML)
        cypher = """
        MATCH (n)
        OPTIONAL MATCH (n)-[r]->()
        RETURN collect(DISTINCT {
            id: n.pattern_id,
            label: COALESCE(n.title, n.cwe_id, ''),
            type: labels(n)[0],
            focus: n.focus,
            weight: r.weight
        }) AS nodes,
        collect(DISTINCT {
            source: startNode(r).pattern_id,
            target: endNode(r).pattern_id,
            type: type(r),
            weight: r.weight
        }) AS edges
        """

        with self._driver.session(database=self.database) as session:
            result = session.run(cypher)
            record = result.single()

            if record:
                data = {
                    "nodes": record.get("nodes", []),
                    "edges": record.get("edges", []),
                    "exported_at": datetime.now(timezone.utc).isoformat(),
                }

                with open(output_path, "w") as f:
                    json.dump(data, f, indent=2)
                logger.info(f"Exported graph analytics to {output_path}")
