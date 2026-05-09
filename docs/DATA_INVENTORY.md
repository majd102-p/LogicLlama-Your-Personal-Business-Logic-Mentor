# LogicLlama Data Inventory

This document is the canonical inventory for the public sources and local reference records used by LogicLlama.

The current release is local-first and deterministic. It does not depend on a trained model to provide useful output today. Instead, it relies on validated public references, curated local records, and deterministic retrieval. If a future model is added, this inventory becomes the baseline for labeled training or evaluation corpora.

## Source Families

| Source | Purpose | Canonical URL | Local Artifact | Status |
| --- | --- | --- | --- | --- |
| CVE Program | Authoritative vulnerability identifiers and lifecycle references | https://www.cve.org/ | Planned sync source | Available |
| NVD | Vulnerability records, CVE details, and CWE mapping | https://nvd.nist.gov/vuln | Live sync source | Available |
| MITRE CWE | Weakness taxonomy and root-cause mapping | https://cwe.mitre.org/ | Snapshot archive + live sync source | Available |
| CISA KEV | Known exploited vulnerabilities catalog | https://www.cisa.gov/known-exploited-vulnerabilities-catalog | Current snapshot archive + live sync source | Available |
| OWASP Top Ten | Public risk baseline and review framework | https://owasp.org/www-project-top-ten/ | [owasp_top_ten_reference.json](../data/fixtures/owasp_top_ten_reference.json) | Bundled reference |
| PortSwigger Access Control | Access-control, privilege escalation, IDOR, and sequence-control guidance | https://portswigger.net/web-security/access-control | [portswigger_access_control_reference.json](../data/fixtures/portswigger_access_control_reference.json) | Bundled reference |
| PortSwigger Business Logic | Workflow, logic-flaw, and state-validation guidance | https://portswigger.net/web-security/logic-flaws | [portswigger_business_logic_reference.json](../data/fixtures/portswigger_business_logic_reference.json) | Bundled reference |

## Historical Coverage Targets

| Source | Historical Scope | Capture Mode |
| --- | --- | --- |
| NVD / CVE | 1999-present | Year backfill via API |
| MITRE CWE | Versioned snapshots where available | Snapshot sync |
| CISA KEV | Dated snapshots plus current feed | Periodic sync |
| OWASP Top Ten | 2007, 2010, 2013, 2017, 2021, 2025 | Curated edition records |
| PortSwigger | Current access-control and business-logic guidance | Curated topic records |

## Bundled Local References

- [owasp_top_ten_reference.json](../data/fixtures/owasp_top_ten_reference.json)
- [portswigger_access_control_reference.json](../data/fixtures/portswigger_access_control_reference.json)
- [portswigger_business_logic_reference.json](../data/fixtures/portswigger_business_logic_reference.json)
- [CWE_SNAPSHOTS_MANIFEST.json](../data/fixtures/cwe_snapshots/CWE_SNAPSHOTS_MANIFEST.json)
- [KEV_SNAPSHOTS_MANIFEST.json](../data/fixtures/kev_snapshots/KEV_SNAPSHOTS_MANIFEST.json)
- [OWASP_EDITIONS_MANIFEST.json](../data/fixtures/owasp_editions/OWASP_EDITIONS_MANIFEST.json)

These records are intentionally small, verified, and reproducible. They are not synthetic placeholders; they are derived from public reference pages and are used to validate the ingestion pipeline, search, reporting, and provenance tracking.

## Acquisition Rules

1. Prefer authoritative public sources over scraped mirrors.
2. Preserve provenance in every `LogicSource` and `LogicCase`.
3. Keep the local reference corpus small enough for deterministic tests.
4. Expand to larger corpora only when the ingestion path has a clear normalization rule and a stable schema.
5. Treat model training as optional until a labeled corpus is explicitly justified.

## Recommended Future Additions

- CVE records for representative business-logic-adjacent weaknesses.
- CWE snapshots for the weakness IDs already mapped in the project.
- KEV records for prioritization examples.
- Additional PortSwigger pages for rate limiting, race conditions, and multi-step workflow flaws.
- Additional OWASP guidance pages for verification and review baselines.