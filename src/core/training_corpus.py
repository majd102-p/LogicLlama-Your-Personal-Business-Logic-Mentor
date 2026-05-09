"""Training corpus generation from LogicCase records."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from .models import LogicCase


class TrainingCorpusExporter:
    """Generates training datasets (Q&A pairs, difficulty scoring) from LogicCase records."""

    def __init__(self) -> None:
        self.corpus: list[dict[str, Any]] = []

    def add_case(self, case: LogicCase) -> None:
        """Extract training examples from a single case."""
        examples = self._extract_examples(case)
        for example in examples:
            self.corpus.append(example)

    def _extract_examples(self, case: LogicCase) -> list[dict[str, Any]]:
        """Generate Q&A pairs from a case."""
        examples: list[dict[str, Any]] = []

        # Core concept question
        examples.append(
            {
                "type": "concept",
                "question": f"What is the primary business logic vulnerability in {case.focus}?",
                "answer": case.summary,
                "context": f"Pattern: {case.pattern_id}",
                "difficulty": "easy",
                "cwe_ids": case.cwe_ids,
                "keywords": case.keywords,
            }
        )

        # Detection question
        examples.append(
            {
                "type": "detection",
                "question": f"How can you detect {case.focus.lower()} vulnerabilities?",
                "answer": f"Look for: {', '.join(case.keywords[:3]) if case.keywords else 'authorization bypasses, state manipulation, workflow gaps'}",
                "context": f"Pattern: {case.pattern_id}",
                "difficulty": "medium",
                "cwe_ids": case.cwe_ids,
                "keywords": case.keywords,
            }
        )

        # Mitigation question
        examples.append(
            {
                "type": "mitigation",
                "question": f"What defenses prevent {case.focus.lower()} attacks?",
                "answer": f"Implement strict state validation, role-based access controls, and workflow integrity checks.",
                "context": f"Pattern: {case.pattern_id}",
                "difficulty": "hard",
                "cwe_ids": case.cwe_ids,
                "keywords": case.keywords,
            }
        )

        # Scenario-based learning
        for i, step in enumerate(case.workflow_steps):
            examples.append(
                {
                    "type": "scenario",
                    "question": f"In {case.focus}, step {i+1} is: {step.title}. What state should be validated?",
                    "answer": step.state_after or "Unknown transition state",
                    "context": f"Pattern: {case.pattern_id}, Step {i+1}",
                    "difficulty": "medium",
                    "cwe_ids": case.cwe_ids,
                    "keywords": case.keywords,
                }
            )

        # Signal-based reasoning
        for signal in case.signals:
            examples.append(
                {
                    "type": "signal",
                    "question": f"What does the signal '{signal.name}' indicate in {case.focus}?",
                    "answer": signal.description or f"Observable indicator: {signal.name}",
                    "context": f"Pattern: {case.pattern_id}, Confidence: {signal.confidence:.2f}",
                    "difficulty": "medium",
                    "cwe_ids": case.cwe_ids,
                    "keywords": case.keywords,
                }
            )

        return examples

    def to_jsonl(self) -> str:
        """Export corpus as JSONL (one JSON object per line)."""
        lines = []
        for example in self.corpus:
            example["exported_at"] = datetime.now(timezone.utc).isoformat()
            lines.append(__import__("json").dumps(example, ensure_ascii=True))
        return "\n".join(lines)

    def to_dict(self) -> dict[str, Any]:
        """Export corpus as a single dict with metadata."""
        return {
            "version": "1.0.0",
            "exported_at": datetime.now(timezone.utc).isoformat(),
            "format": "training_corpus",
            "total_examples": len(self.corpus),
            "examples": self.corpus,
        }

    def statistics(self) -> dict[str, Any]:
        """Return corpus statistics."""
        type_counts = {}
        difficulty_counts = {}
        for ex in self.corpus:
            ex_type = ex.get("type", "unknown")
            difficulty = ex.get("difficulty", "unknown")
            type_counts[ex_type] = type_counts.get(ex_type, 0) + 1
            difficulty_counts[difficulty] = difficulty_counts.get(difficulty, 0) + 1

        return {
            "total_examples": len(self.corpus),
            "by_type": type_counts,
            "by_difficulty": difficulty_counts,
        }
