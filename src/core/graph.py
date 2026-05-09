"""Persistent knowledge graph for LogicLlama case relationships."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Any


class GraphRelationType(StrEnum):
    """Semantic relationship types in the LogicLlama knowledge graph."""

    DERIVED_FROM = "derived_from"  # pattern_id → source
    MAPS_TO = "maps_to"  # pattern_id → cwe_id
    SUPPORTS = "supports"  # signal → pattern_id
    EXPLOITS = "exploits"  # pattern_id → vulnerability
    RELATED_TO = "related_to"  # pattern_id ↔ pattern_id (similar logic)
    VARIANT_OF = "variant_of"  # pattern_id → pattern_id (specialization)


class GraphNodeType(StrEnum):
    """Node classifications for graph entities."""

    CASE = "case"  # LogicLlama case (pattern_id)
    CWE = "cwe"  # Common Weakness Enumeration
    SIGNAL = "signal"  # Observable/detectable signal
    SOURCE = "source"  # Data source (NVD, KEV, etc.)
    PLATFORM = "platform"  # Platform or product (e.g., Django, Spring)
    TACTIC = "tactic"  # Attack/defense tactic


@dataclass(frozen=True)
class GraphNode:
    """Vertex in the knowledge graph."""

    node_id: str
    node_type: GraphNodeType
    label: str
    description: str | None = None
    metadata: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "node_id": self.node_id,
            "node_type": self.node_type.value,
            "label": self.label,
            "description": self.description,
            "metadata": self.metadata or {},
        }


@dataclass(frozen=True)
class GraphEdge:
    """Directed edge in the knowledge graph."""

    from_node_id: str
    to_node_id: str
    relation_type: GraphRelationType
    weight: float | None = None  # 0.0-1.0 for confidence/relevance
    metadata: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "from": self.from_node_id,
            "to": self.to_node_id,
            "relation": self.relation_type.value,
            "weight": self.weight,
            "metadata": self.metadata or {},
        }


@dataclass
class GraphQuery:
    """Query specification for graph traversal."""

    start_node_id: str
    relation_types: list[GraphRelationType] | None = None
    max_depth: int = 2
    node_types: list[GraphNodeType] | None = None


@dataclass
class GraphTraversalResult:
    """Results from graph traversal query."""

    query: GraphQuery
    nodes: list[GraphNode]
    edges: list[GraphEdge]
    traversed_count: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "query": {
                "start_node_id": self.query.start_node_id,
                "relation_types": [r.value for r in (self.query.relation_types or [])],
                "max_depth": self.query.max_depth,
                "node_types": [n.value for n in (self.query.node_types or [])],
            },
            "nodes": [n.to_dict() for n in self.nodes],
            "edges": [e.to_dict() for e in self.edges],
            "traversed_count": self.traversed_count,
        }


class GraphQueryEngine:
    """In-memory graph query execution engine."""

    def __init__(self, nodes: list[GraphNode], edges: list[GraphEdge]) -> None:
        self.nodes = {n.node_id: n for n in nodes}
        self.edges = edges
        self._build_adjacency()

    def _build_adjacency(self) -> None:
        """Build adjacency structures for efficient traversal."""
        self.forward: dict[str, list[GraphEdge]] = {}
        self.reverse: dict[str, list[GraphEdge]] = {}
        for edge in self.edges:
            if edge.from_node_id not in self.forward:
                self.forward[edge.from_node_id] = []
            self.forward[edge.from_node_id].append(edge)
            if edge.to_node_id not in self.reverse:
                self.reverse[edge.to_node_id] = []
            self.reverse[edge.to_node_id].append(edge)

    def traverse(self, query: GraphQuery) -> GraphTraversalResult:
        """Execute BFS graph traversal from start_node_id."""
        if query.start_node_id not in self.nodes:
            return GraphTraversalResult(query=query, nodes=[], edges=[], traversed_count=0)

        visited: set[str] = set()
        queue: list[tuple[str, int]] = [(query.start_node_id, 0)]
        result_nodes: dict[str, GraphNode] = {}
        result_edges: set[tuple[str, str, str]] = set()
        traversed_count = 0

        while queue:
            node_id, depth = queue.pop(0)
            if node_id in visited or depth > query.max_depth:
                continue
            visited.add(node_id)
            traversed_count += 1

            if node_id in self.nodes:
                node = self.nodes[node_id]
                if query.node_types is None or node.node_type in query.node_types:
                    result_nodes[node_id] = node

            if depth < query.max_depth:
                for edge in self.forward.get(node_id, []):
                    if query.relation_types is None or edge.relation_type in query.relation_types:
                        result_edges.add((edge.from_node_id, edge.to_node_id, edge.relation_type.value))
                        if edge.to_node_id not in visited:
                            queue.append((edge.to_node_id, depth + 1))

        result_edge_objs = [
            e for e in self.edges
            if (e.from_node_id, e.to_node_id, e.relation_type.value) in result_edges
        ]

        return GraphTraversalResult(
            query=query,
            nodes=list(result_nodes.values()),
            edges=result_edge_objs,
            traversed_count=traversed_count,
        )

    def neighbors(self, node_id: str, relation_types: list[GraphRelationType] | None = None) -> list[GraphNode]:
        """Get immediate neighbors of a node."""
        neighbors = []
        for edge in self.forward.get(node_id, []):
            if relation_types is None or edge.relation_type in relation_types:
                if edge.to_node_id in self.nodes:
                    neighbors.append(self.nodes[edge.to_node_id])
        return neighbors

    def get_node(self, node_id: str) -> GraphNode | None:
        """Retrieve a single node."""
        return self.nodes.get(node_id)
