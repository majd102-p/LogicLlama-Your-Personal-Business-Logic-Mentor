"""Simulation corpus generation from LogicCase records."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from .models import LogicCase


class SimulationCorpusExporter:
    """Generates simulation test cases and attack scenarios from LogicCase records."""

    def __init__(self) -> None:
        self.simulations: list[dict[str, Any]] = []

    def add_case(self, case: LogicCase) -> None:
        """Extract simulation scenarios from a single case."""
        simulations = self._generate_simulations(case)
        self.simulations.extend(simulations)

    def _generate_simulations(self, case: LogicCase) -> list[dict[str, Any]]:
        """Generate executable test scenarios."""
        simulations: list[dict[str, Any]] = []

        # Basic state transition test
        simulations.append(
            {
                "type": "state_transition",
                "pattern_id": case.pattern_id,
                "focus": case.focus,
                "scenario": f"Verify valid workflow: {' -> '.join([s.title for s in case.workflow_steps][:3])}",
                "preconditions": [s.state_before or "initial_state" for s in case.workflow_steps[:1]],
                "attack_steps": [],
                "expected_result": "Valid transitions should succeed",
                "test_vector": "legitimate_flow",
                "severity": "info",
            }
        )

        # Out-of-order execution test
        if len(case.workflow_steps) > 1:
            simulations.append(
                {
                    "type": "workflow_bypass",
                    "pattern_id": case.pattern_id,
                    "focus": case.focus,
                    "scenario": f"Attempt out-of-order step execution in {case.focus}",
                    "preconditions": ["initial_state"],
                    "attack_steps": [
                        f"Skip to step: {case.workflow_steps[-1].title}",
                        f"Bypass steps: {', '.join([s.title for s in case.workflow_steps[:-1]])}",
                    ],
                    "expected_result": "Should fail due to missing prior state",
                    "test_vector": "workflow_skip",
                    "severity": "high",
                    "cwe_ids": case.cwe_ids,
                }
            )

        # Race condition test
        simulations.append(
            {
                "type": "concurrency",
                "pattern_id": case.pattern_id,
                "focus": case.focus,
                "scenario": f"Parallel execution of {case.focus} workflow steps",
                "preconditions": ["initial_state"],
                "attack_steps": [
                    f"Execute step 1: {case.workflow_steps[0].title if case.workflow_steps else 'step1'}",
                    f"Execute step 2 (concurrent): {case.workflow_steps[1].title if len(case.workflow_steps) > 1 else 'step2'}",
                    "Verify state consistency",
                ],
                "expected_result": "State should be consistent despite concurrency",
                "test_vector": "race_condition",
                "severity": "high",
                "cwe_ids": ["CWE-362"] + case.cwe_ids,
            }
        )

        # Authorization bypass test
        simulations.append(
            {
                "type": "authorization",
                "pattern_id": case.pattern_id,
                "focus": case.focus,
                "scenario": f"Attempt unauthorized {case.focus.lower()} access",
                "preconditions": ["unprivileged_user"],
                "attack_steps": [
                    "Assume unprivileged user role",
                    "Attempt restricted action",
                    "Check for privilege escalation",
                ],
                "expected_result": "Access should be denied",
                "test_vector": "unauthorized_action",
                "severity": "critical",
                "cwe_ids": ["CWE-639"] + case.cwe_ids,
            }
        )

        # Signal-based detection test
        for signal in case.signals[:2]:
            simulations.append(
                {
                    "type": "detection",
                    "pattern_id": case.pattern_id,
                    "focus": case.focus,
                    "scenario": f"Trigger signal: {signal.name} ({signal.description or 'unknown'})",
                    "preconditions": ["exploit_triggered"],
                    "attack_steps": [
                        f"Execute exploit vector for: {signal.name}",
                        "Monitor for signal emission",
                    ],
                    "expected_result": f"Signal '{signal.name}' should be emitted",
                    "test_vector": signal.name,
                    "severity": "medium",
                    "signal_confidence": signal.confidence,
                    "cwe_ids": case.cwe_ids,
                }
            )

        return simulations

    def to_jsonl(self) -> str:
        """Export as JSONL."""
        lines = []
        for sim in self.simulations:
            sim["exported_at"] = datetime.now(timezone.utc).isoformat()
            lines.append(__import__("json").dumps(sim, ensure_ascii=True))
        return "\n".join(lines)

    def to_dict(self) -> dict[str, Any]:
        """Export as a single dict with metadata."""
        return {
            "version": "1.0.0",
            "exported_at": datetime.now(timezone.utc).isoformat(),
            "format": "simulation_corpus",
            "total_simulations": len(self.simulations),
            "simulations": self.simulations,
        }

    def statistics(self) -> dict[str, Any]:
        """Return corpus statistics."""
        type_counts = {}
        severity_counts = {}
        for sim in self.simulations:
            sim_type = sim.get("type", "unknown")
            severity = sim.get("severity", "unknown")
            type_counts[sim_type] = type_counts.get(sim_type, 0) + 1
            severity_counts[severity] = severity_counts.get(severity, 0) + 1

        return {
            "total_simulations": len(self.simulations),
            "by_type": type_counts,
            "by_severity": severity_counts,
        }
