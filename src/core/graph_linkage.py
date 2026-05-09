"""Cross-case graph linking with similarity heuristics."""

from __future__ import annotations

from typing import Any
from .models import LogicCase
from .graph import GraphNode, GraphEdge, GraphNodeType, GraphRelationType


def compute_case_similarity(case_a: LogicCase, case_b: LogicCase) -> float:
    """Compute similarity score between two cases (0.0 to 1.0)."""
    if case_a.pattern_id == case_b.pattern_id:
        return 1.0

    score = 0.0

    # Focus similarity (0-0.3)
    if case_a.focus == case_b.focus:
        score += 0.3

    # CWE overlap (0-0.3)
    cwe_set_a = set(case_a.cwe_ids)
    cwe_set_b = set(case_b.cwe_ids)
    if cwe_set_a and cwe_set_b:
        intersection = len(cwe_set_a & cwe_set_b)
        union = len(cwe_set_a | cwe_set_b)
        if union > 0:
            score += 0.3 * (intersection / union)

    # Keyword overlap (0-0.2)
    keyword_set_a = set(case_a.keywords)
    keyword_set_b = set(case_b.keywords)
    if keyword_set_a and keyword_set_b:
        intersection = len(keyword_set_a & keyword_set_b)
        union = len(keyword_set_a | keyword_set_b)
        if union > 0:
            score += 0.2 * (intersection / union)

    # Source type similarity (0-0.2)
    if case_a.source_type == case_b.source_type:
        score += 0.1
    # Also credit similar source types (both NVD and KEV are public sources)
    elif {case_a.source_type, case_b.source_type} <= {"nvd", "kev"}:
        score += 0.05

    return min(score, 1.0)


def build_cross_case_edges(cases: list[LogicCase], similarity_threshold: float = 0.3) -> list[GraphEdge]:
    """Generate edges between similar cases."""
    edges: list[GraphEdge] = []

    for i, case_a in enumerate(cases):
        for case_b in cases[i + 1 :]:
            similarity = compute_case_similarity(case_a, case_b)

            if similarity >= similarity_threshold:
                # Determine relation type based on similarity
                if similarity >= 0.7:
                    relation = GraphRelationType.VARIANT_OF
                else:
                    relation = GraphRelationType.RELATED_TO

                # Create bidirectional edge
                edges.append(
                    GraphEdge(
                        from_node_id=case_a.pattern_id,
                        to_node_id=case_b.pattern_id,
                        relation_type=relation,
                        weight=similarity,
                        metadata={"similarity_score": similarity},
                    )
                )

    return edges


def export_to_networkx(nodes: list[GraphNode], edges: list[GraphEdge]) -> dict[str, Any]:
    """Export graph as networkx-compatible JSON (nodes/links format)."""
    node_dict = {}
    for node in nodes:
        node_dict[node.node_id] = {
            "id": node.node_id,
            "type": node.node_type.value,
            "label": node.label,
            "description": node.description,
            "metadata": node.metadata or {},
        }

    links = []
    for edge in edges:
        links.append(
            {
                "source": edge.from_node_id,
                "target": edge.to_node_id,
                "relation": edge.relation_type.value,
                "weight": edge.weight or 1.0,
                "metadata": edge.metadata or {},
            }
        )

    return {
        "directed": True,
        "multigraph": False,
        "graph": {"format": "networkx_json"},
        "nodes": list(node_dict.values()),
        "links": links,
    }
