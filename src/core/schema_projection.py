"""Projection helpers that map current LogicCase records onto the MASTER_SCHEMA shape."""

from __future__ import annotations

from typing import Any

from .master_schema import MasterSchemaProjection
from .models import LogicCase, LogicSource


def build_master_schema_projection(logic_case: LogicCase, source: LogicSource | None = None) -> dict[str, Any]:
    focus = _normalize_focus(logic_case)
    source_type = logic_case.source_type.value
    source_title = source.title if source is not None else logic_case.title
    source_uri = source.uri if source is not None else ""

    source_ids = list(logic_case.source_ids)
    cwe_ids = list(logic_case.cwe_ids)
    keywords = list(logic_case.keywords)
    signal_names = [signal.name for signal in logic_case.signals]
    step_titles = [step.title for step in logic_case.workflow_steps]

    projection = {
        "schema_version": "1.0.0",
        "pattern_id": logic_case.pattern_id,
        "metadata": {
            **logic_case.metadata,
            "source_type": source_type,
            "source_title": source_title,
            "source_uri": source_uri,
            "projection": "logic_case_to_master_schema",
        },
        "title": logic_case.title,
        "focus": focus,
        "search_index": _build_search_index(logic_case, source),
        "core_concept": _build_core_concept(logic_case, focus),
        "logic_flow": _build_logic_flow(logic_case, step_titles),
        "attack_model": _build_attack_model(logic_case, source_ids, focus),
        "developer_mindset": _build_developer_mindset(logic_case),
        "data_points": _build_data_points(logic_case, source),
        "comparative_analysis": [],
        "training": _build_training(logic_case),
        "user_feedback": {"common_mistakes": [], "expected_wrong_answers": []},
        "arsenal": _build_arsenal(logic_case),
        "impact": _build_impact(logic_case, focus),
        "graph_relations": _build_graph_relations(logic_case, source_ids, cwe_ids, signal_names),
        "detection": _build_detection(logic_case, signal_names),
        "mitigation": _build_mitigation(logic_case, focus),
        "execution_context": _build_execution_context(logic_case, source_uri),
        "timing": _build_timing(logic_case),
        "ai_features": _build_ai_features(logic_case, focus),
        "risk_score": _build_risk_score(logic_case),
        "real_world_mapping": _build_real_world_mapping(logic_case, focus),
        "simulation": _build_simulation(logic_case),
        "inference_rules": [],
        "decision_logic": _build_decision_logic(logic_case, focus, signal_names),
    }

    return MasterSchemaProjection.model_validate(projection).model_dump(mode="json")


def _normalize_focus(logic_case: LogicCase) -> str:
    text = " ".join([logic_case.focus, logic_case.title, logic_case.summary, " ".join(logic_case.keywords)]).lower()
    if "access" in text or logic_case.source_type.value in {"portswigger", "owasp"}:
        return "Access Control"
    if "race" in text:
        return "Race Condition"
    if "state" in text:
        return "State Manipulation"
    if "trust" in text:
        return "Trust Boundary Violation"
    if "workflow" in text or "logic" in text or "bypass" in text:
        return "Workflow Bypass"
    return "Business Logic"


def _build_search_index(logic_case: LogicCase, source: LogicSource | None) -> dict[str, list[str]]:
    entities = list(dict.fromkeys([*logic_case.source_ids, *logic_case.cwe_ids]))
    if source is not None:
        entities = list(dict.fromkeys([source.source_id, *entities]))
    intent_tags = [logic_case.source_type.value, _normalize_focus(logic_case).replace(" ", "_").lower()]
    return {
        "keywords": logic_case.keywords,
        "entities": entities,
        "intent_tags": intent_tags,
    }


def _build_core_concept(logic_case: LogicCase, focus: str) -> dict[str, Any]:
    return {
        "cwe_id": logic_case.cwe_ids[0] if logic_case.cwe_ids else "",
        "logic_type": focus,
        "abstraction": logic_case.summary[:160],
        "industry_tags": [],
    }


def _build_logic_flow(logic_case: LogicCase, step_titles: list[str]) -> dict[str, Any]:
    intended = [f"Validate {logic_case.focus.lower()}", f"Preserve {logic_case.source_type.value} provenance"]
    actual = [logic_case.summary]
    breakpoint = logic_case.metadata.get("breakpoint", logic_case.summary[:120])
    state_machine = [
        {"state": step.state_before or "unknown", "transition": step.title} for step in logic_case.workflow_steps
    ]
    if not state_machine and step_titles:
        state_machine = [{"state": "observed", "transition": title} for title in step_titles]
    return {
        "intended": intended,
        "actual": actual,
        "breakpoint": breakpoint,
        "state_machine": state_machine,
    }


def _build_attack_model(logic_case: LogicCase, source_ids: list[str], focus: str) -> dict[str, Any]:
    entry_points = source_ids or [logic_case.pattern_id]
    attack_steps = [step.title for step in logic_case.workflow_steps] or [logic_case.summary]
    bypass_type = {
        "Access Control": "Authorization",
        "Workflow Bypass": "Workflow",
        "Race Condition": "State",
        "State Manipulation": "State",
        "Trust Boundary Violation": "Validation",
    }.get(focus, "Validation")
    return {
        "attacker_goal": logic_case.focus,
        "entry_points": entry_points,
        "attack_steps": attack_steps,
        "attack_graph": [{"node": logic_case.pattern_id, "next": attack_steps[:3]}],
        "bypass_type": bypass_type,
    }


def _build_developer_mindset(logic_case: LogicCase) -> dict[str, str]:
    return {
        "false_assumption": f"{logic_case.focus} is fully enforced by default.",
        "missed_edge_case": "A valid workflow can still be abused through ordering or ownership changes.",
        "design_flaw": logic_case.summary[:160],
        "why_it_happens": "The runtime preserves a concise evidence record, but the full application context still needs to be modeled explicitly.",
    }


def _build_data_points(logic_case: LogicCase, source: LogicSource | None) -> dict[str, Any]:
    cves: list[dict[str, Any]] = []
    if logic_case.source_type.value == "nvd":
        for source_id in logic_case.source_ids:
            if source_id.startswith("CVE-"):
                parts = source_id.split("-")
                year = int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else 0
                cves.append({"cve_id": source_id, "year": year, "context": logic_case.summary, "impact": logic_case.focus})
    writeups = []
    if source is not None:
        writeups.append({"source": source.title, "url": source.uri})
    return {"cves": cves, "writeups": writeups}


def _build_training(logic_case: LogicCase) -> dict[str, Any]:
    return {
        "scenario": logic_case.summary,
        "questions": [f"What makes {logic_case.focus.lower()} relevant here?"],
        "hints": logic_case.keywords[:3],
        "solution": "Use the provenance trail and the workflow context to explain the pattern.",
        "evaluation": {
            "correct_criteria": ["Mentions the workflow or control that fails", "Connects the case to its CWE or source evidence"],
            "scoring_logic": "score = evidence_match + workflow_alignment",
        },
    }


def _build_arsenal(logic_case: LogicCase) -> dict[str, Any]:
    return {
        "tools": [logic_case.source_type.value, "sqlite", "cli"],
        "techniques": ["ingestion", "taxonomy mapping", "evidence tracking"],
        "automation_level": "Semi",
    }


def _build_impact(logic_case: LogicCase, focus: str) -> dict[str, str]:
    return {
        "technical": logic_case.summary,
        "business": f"Creates weakness in {focus.lower()} controls.",
        "financial": "Potential abuse of trust, access, or process integrity.",
        "exploitability": f"Derived from {logic_case.source_type.value} evidence and normalized signals.",
    }


def _build_graph_relations(
    logic_case: LogicCase,
    source_ids: list[str],
    cwe_ids: list[str],
    signal_names: list[str],
) -> dict[str, Any]:
    nodes = [logic_case.pattern_id, *source_ids, *cwe_ids, *signal_names]
    edges = []
    for source_id in source_ids:
        edges.append({"from": logic_case.pattern_id, "to": source_id, "relation": "derived_from"})
    for cwe_id in cwe_ids:
        edges.append({"from": logic_case.pattern_id, "to": cwe_id, "relation": "maps_to"})
    for signal_name in signal_names:
        edges.append({"from": signal_name, "to": logic_case.pattern_id, "relation": "supports"})
    return {"nodes": list(dict.fromkeys(nodes)), "edges": edges}


def _build_detection(logic_case: LogicCase, signal_names: list[str]) -> dict[str, list[str]]:
    return {
        "manual_signals": signal_names,
        "automated_rules": logic_case.keywords[:3],
        "log_patterns": [logic_case.focus, logic_case.source_type.value],
        "code_smells": ["missing authorization", "weak validation", "workflow bypass"],
    }


def _build_mitigation(logic_case: LogicCase, focus: str) -> dict[str, Any]:
    return {
        "secure_design": f"Model and enforce {focus.lower()} explicitly.",
        "code_fix": "Add validation, provenance checks, and explicit state transitions.",
        "validation_rules": ["Verify workflow prerequisites", "Track ownership and state transitions"],
        "monitoring": f"Alert on anomalous {logic_case.focus.lower()} patterns and repeated failed transitions.",
    }


def _build_execution_context(logic_case: LogicCase, source_uri: str) -> dict[str, Any]:
    protocol = "HTTP" if logic_case.source_type.value in {"nvd", "kev", "portswigger", "owasp"} else "gRPC"
    return {
        "protocol": protocol,
        "endpoint_example": source_uri,
        "request_sample": logic_case.summary,
        "response_sample": "Observed evidence preserved in the normalized case.",
        "request_variants": [],
    }


def _build_timing(logic_case: LogicCase) -> dict[str, Any]:
    return {
        "is_time_sensitive": any(signal.name in {"latency_spike", "duplicate_transaction"} for signal in logic_case.signals),
        "race_window": "unknown",
        "parallelism_factor": 1.0,
    }


def _build_ai_features(logic_case: LogicCase, focus: str) -> dict[str, Any]:
    return {
        "difficulty": "Intermediate" if logic_case.signals else "Beginner",
        "embedding_tags": logic_case.keywords,
        "similarity_group": focus,
        "prerequisites": [logic_case.source_type.value],
    }


def _build_risk_score(logic_case: LogicCase) -> dict[str, Any]:
    base = round(logic_case.confidence, 2)
    business_weight = round(min(1.0, 0.1 * len(logic_case.cwe_ids)), 2)
    exploitability = round(min(1.0, base + business_weight / 2), 2)
    final_score = round(min(1.0, base * 0.6 + business_weight * 0.2 + exploitability * 0.2), 2)
    return {
        "base": base,
        "business_weight": business_weight,
        "exploitability": exploitability,
        "final_score": final_score,
    }


def _build_real_world_mapping(logic_case: LogicCase, focus: str) -> list[dict[str, str]]:
    return [
        {
            "platform_type": logic_case.source_type.value,
            "implementation_pattern": focus,
            "failure_reason": "The data source encodes a reusable pattern rather than a complete product-specific exploit path.",
        }
    ]


def _build_simulation(logic_case: LogicCase) -> dict[str, Any]:
    return {
        "attack_script": "",
        "expected_result": logic_case.summary,
        "failure_conditions": ["missing evidence", "no workflow context", "invalid source mapping"],
    }


def _build_decision_logic(logic_case: LogicCase, focus: str, signal_names: list[str]) -> dict[str, Any]:
    return {
        "priority_signals": signal_names or [logic_case.focus],
        "next_best_action": [f"Review {focus.lower()} evidence", "Correlate with CWE taxonomy", "Preserve provenance"],
    }