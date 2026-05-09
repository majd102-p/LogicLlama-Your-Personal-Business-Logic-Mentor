"""Graph builder that syncs case relationships into the knowledge graph."""

from __future__ import annotations

from .models import LogicCase
from .graph import GraphNode, GraphEdge, GraphNodeType, GraphRelationType
from .storage import SQLiteLogicStore


class GraphBuilder:
    """Builds and maintains the knowledge graph from LogicCase records."""

    def __init__(self, store: SQLiteLogicStore) -> None:
        self.store = store

    def build_graph_from_case(self, case: LogicCase) -> tuple[list[GraphNode], list[GraphEdge]]:
        """Extract graph nodes and edges from a LogicCase."""
        nodes: list[GraphNode] = []
        edges: list[GraphEdge] = []

        # Create node for the case itself
        case_node = GraphNode(
            node_id=case.pattern_id,
            node_type=GraphNodeType.CASE,
            label=case.title,
            description=case.summary,
            metadata={"focus": case.focus, "keywords": case.keywords},
        )
        nodes.append(case_node)

        # Create nodes and edges for CWE IDs
        for cwe_id in case.cwe_ids:
            cwe_node = GraphNode(
                node_id=cwe_id,
                node_type=GraphNodeType.CWE,
                label=cwe_id,
                metadata={"extracted_from": case.pattern_id},
            )
            nodes.append(cwe_node)
            edges.append(
                GraphEdge(
                    from_node_id=case.pattern_id,
                    to_node_id=cwe_id,
                    relation_type=GraphRelationType.MAPS_TO,
                    weight=0.9,
                )
            )

        # Create nodes and edges for source IDs
        for source_id in case.source_ids:
            source_node = GraphNode(
                node_id=source_id,
                node_type=GraphNodeType.SOURCE,
                label=source_id,
                metadata={"extracted_from": case.pattern_id},
            )
            nodes.append(source_node)
            edges.append(
                GraphEdge(
                    from_node_id=case.pattern_id,
                    to_node_id=source_id,
                    relation_type=GraphRelationType.DERIVED_FROM,
                    weight=0.8,
                )
            )

        # Create nodes and edges for signals
        for signal in case.signals:
            signal_node = GraphNode(
                node_id=signal.name,
                node_type=GraphNodeType.SIGNAL,
                label=signal.name,
                description=signal.description,
                metadata={"confidence": signal.confidence},
            )
            nodes.append(signal_node)
            edges.append(
                GraphEdge(
                    from_node_id=signal.name,
                    to_node_id=case.pattern_id,
                    relation_type=GraphRelationType.SUPPORTS,
                    weight=float(signal.confidence),
                )
            )

        # Create nodes for focus area / tactic
        focus_normalized = case.focus.replace(" ", "_").lower()
        focus_node = GraphNode(
            node_id=f"tactic_{focus_normalized}",
            node_type=GraphNodeType.TACTIC,
            label=case.focus,
            metadata={"extracted_from": case.pattern_id},
        )
        nodes.append(focus_node)
        edges.append(
            GraphEdge(
                from_node_id=case.pattern_id,
                to_node_id=focus_node.node_id,
                relation_type=GraphRelationType.RELATED_TO,
                weight=0.7,
            )
        )

        return nodes, edges

    def sync_case_graph(self, case: LogicCase) -> None:
        """Sync a case's relationships into the knowledge graph."""
        nodes, edges = self.build_graph_from_case(case)
        for node in nodes:
            self.store.upsert_graph_node(node)
        for edge in edges:
            self.store.upsert_graph_edge(edge)

    def sync_all_cases(self) -> int:
        """Rebuild the entire graph from all stored cases."""
        cases = self.store.list_cases(limit=10000)
        count = 0
        for case in cases:
            self.sync_case_graph(case)
            count += 1
        return count
