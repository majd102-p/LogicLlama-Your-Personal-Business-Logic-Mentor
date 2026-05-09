"""Adapters that normalize public security sources into LogicLlama records."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import requests

from src.core import EvidenceItem, LogicCase, LogicCaseStatus, LogicSignal, LogicSource, LogicSourceType, LogicStep


@dataclass(frozen=True, slots=True)
class SourceRecord:
    source: LogicSource
    case: LogicCase


def _first_description_text(descriptions: list[dict[str, Any]] | None) -> str:
    if not descriptions:
        return "No description available."
    for item in descriptions:
        text = str(item.get("value", "")).strip()
        if text:
            return text
    return "No description available."


class NVDAdapter:
    """Normalize NVD CVE records."""

    source_type = LogicSourceType.NVD

    def normalize(self, cve_item: dict[str, Any]) -> SourceRecord:
        cve = cve_item.get("cve", cve_item)
        cve_id = str(cve.get("id") or cve_item.get("cveId") or "unknown-cve")
        descriptions = cve.get("descriptions", [])
        source = LogicSource(
            source_id=cve_id,
            source_type=self.source_type,
            title=cve_id,
            uri=f"https://nvd.nist.gov/vuln/detail/{cve_id}",
            license="Public domain data from NVD",
            metadata={"source": "NVD", "raw": {"cve": cve}},
        )
        case = LogicCase(
            pattern_id=f"LOGIC-NVD-{cve_id.replace('CVE-', '').replace('-', '')[:12]}",
            title=cve_id,
            focus="Vulnerability Intelligence",
            summary=_first_description_text(descriptions),
            source_type=self.source_type,
            source_ids=[cve_id],
            cwe_ids=self._extract_cwe_ids(cve),
            keywords=self._extract_keywords(cve),
            signals=self._extract_signals(cve),
            workflow_steps=[],
            evidence=[
                EvidenceItem(
                    evidence_id=f"{cve_id}:evidence",
                    summary="Imported from NVD CVE record",
                    source_id=cve_id,
                    evidence_type="cve_record",
                    metadata={"raw_id": cve_id},
                )
            ],
            status=LogicCaseStatus.validated,
            confidence=self._extract_confidence(cve),
            metadata={"source": "NVD", "raw": cve_item},
        )
        return SourceRecord(source=source, case=case)

    @staticmethod
    def _extract_cwe_ids(cve: dict[str, Any]) -> list[str]:
        cwe_ids: list[str] = []
        weaknesses = cve.get("weaknesses", [])
        for weakness in weaknesses:
            for description in weakness.get("description", []):
                cwe = str(description.get("value", "")).strip()
                if cwe:
                    cwe_ids.append(cwe)
        return list(dict.fromkeys(cwe_ids))

    @staticmethod
    def _extract_keywords(cve: dict[str, Any]) -> list[str]:
        keywords: set[str] = set()
        for cwe_id in NVDAdapter._extract_cwe_ids(cve):
            keywords.add(cwe_id.lower())
        descriptions = cve.get("descriptions", [])
        if descriptions:
            text = _first_description_text(descriptions)
            for token in text.replace("/", " ").replace(",", " ").split():
                cleaned = token.strip().lower()
                if len(cleaned) > 4:
                    keywords.add(cleaned)
        return sorted(keywords)

    @staticmethod
    def _extract_signals(cve: dict[str, Any]) -> list[LogicSignal]:
        signals: list[LogicSignal] = []
        metrics = cve.get("metrics", {})
        if metrics:
            signals.append(
                LogicSignal(
                    name="has_metrics",
                    value=True,
                    confidence=0.9,
                    description="NVD record contains metrics",
                    metadata={"metrics": metrics},
                )
            )
        return signals

    @staticmethod
    def _extract_confidence(cve: dict[str, Any]) -> float:
        metrics = cve.get("metrics", {})
        if metrics:
            return 0.9
        return 0.6


class KEVAdapter:
    """Normalize CISA KEV entries."""

    source_type = LogicSourceType.KEV

    def normalize(self, kev_item: dict[str, Any]) -> SourceRecord:
        cve_id = str(kev_item.get("cveID") or kev_item.get("cve_id") or "unknown-kev")
        source = LogicSource(
            source_id=cve_id,
            source_type=self.source_type,
            title=cve_id,
            uri="https://www.cisa.gov/known-exploited-vulnerabilities-catalog",
            license="Public government data from CISA",
            metadata={"source": "CISA KEV", "raw": kev_item},
        )
        summary = str(kev_item.get("shortDescription") or kev_item.get("vendorProject") or cve_id)
        case = LogicCase(
            pattern_id=f"LOGIC-KEV-{cve_id.replace('CVE-', '').replace('-', '')[:12]}",
            title=summary,
            focus="Exploitation Priority",
            summary=summary,
            source_type=self.source_type,
            source_ids=[cve_id],
            cwe_ids=[],
            keywords=sorted(["kev", "exploited", "priority"]),
            signals=[
                LogicSignal(
                    name="known_exploited",
                    value=True,
                    confidence=1.0,
                    description="Present in CISA KEV catalog",
                    metadata={"ransomwareUse": kev_item.get("knownRansomwareCampaignUse")},
                )
            ],
            workflow_steps=[],
            evidence=[
                EvidenceItem(
                    evidence_id=f"{cve_id}:kev",
                    summary="Imported from CISA KEV catalog",
                    source_id=cve_id,
                    evidence_type="kev_record",
                    metadata={"raw_id": cve_id},
                )
            ],
            status=LogicCaseStatus.validated,
            confidence=1.0,
            metadata={"source": "CISA KEV", "raw": kev_item},
        )
        return SourceRecord(source=source, case=case)


class CWEAdapter:
    """Normalize CWE entries into searchable case records."""

    source_type = LogicSourceType.CWE

    def normalize(self, cwe_item: dict[str, Any]) -> SourceRecord:
        cwe_id = str(cwe_item.get("id") or cwe_item.get("cwe_id") or "unknown-cwe")
        title = str(cwe_item.get("name") or cwe_id)
        source = LogicSource(
            source_id=cwe_id,
            source_type=self.source_type,
            title=title,
            uri=f"https://cwe.mitre.org/data/definitions/{cwe_id.replace('CWE-', '')}.html",
            license="MITRE CWE terms of use",
            metadata={"source": "MITRE CWE", "raw": cwe_item},
        )
        case = LogicCase(
            pattern_id=f"LOGIC-CWE-{cwe_id.replace('CWE-', '').replace('-', '')[:12]}",
            title=title,
            focus="Weakness Taxonomy",
            summary=str(cwe_item.get("description") or title),
            source_type=self.source_type,
            source_ids=[cwe_id],
            cwe_ids=[cwe_id],
            keywords=[title.lower(), "cwe"],
            signals=[],
            workflow_steps=[],
            evidence=[
                EvidenceItem(
                    evidence_id=f"{cwe_id}:cwe",
                    summary="Imported from CWE taxonomy",
                    source_id=cwe_id,
                    evidence_type="taxonomy_record",
                    metadata={"raw_id": cwe_id},
                )
            ],
            status=LogicCaseStatus.validated,
            confidence=0.85,
            metadata={"source": "MITRE CWE", "raw": cwe_item},
        )
        return SourceRecord(source=source, case=case)


def fetch_json(url: str, params: dict[str, Any] | None = None, headers: dict[str, str] | None = None) -> dict[str, Any]:
    response = requests.get(url, params=params, headers=headers, timeout=30)
    response.raise_for_status()
    return response.json()
