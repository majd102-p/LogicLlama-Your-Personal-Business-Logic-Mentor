# Historical Coverage Plan

This document defines the historical coverage LogicLlama aims to collect for business-logic-focused analysis.

The scope is intentionally narrow: collect authoritative vulnerability and workflow references across the full available history, but prioritize data that helps explain business-logic failures, access-control mistakes, workflow bypasses, and state-validation gaps.

## Coverage Targets

### NVD / CVE

- Scope: full available NVD history from 1999 to present.
- Collection mode: year-range backfill using the NVD CVE API.
- Purpose: establish a complete CVE corpus and map CVE records to CWE and business-logic-adjacent patterns.

### MITRE CWE

- Scope: current taxonomy plus available versioned snapshots.
- Collection mode: periodic snapshot sync and manual archival capture.
- Purpose: map weaknesses to the internal reasoning graph.

### CISA KEV

- Scope: current catalog plus dated snapshots captured over time.
- Collection mode: regular sync and archived snapshots.
- Purpose: weight exploitable findings by real-world exploitation signal.

### OWASP Top Ten

- Scope: historical Top Ten editions currently relevant to application security review.
- Editions to retain:
  - 2007
  - 2010
  - 2013
  - 2017
  - 2021
  - 2025
- Purpose: provide a risk baseline across the years.

### PortSwigger Web Security Academy

- Scope: access-control and business-logic topics, with broader expansion into related logic-flaw areas.
- Collection mode: curated topic references and selected lab guidance.
- Purpose: preserve real workflow and access-control reasoning examples.

## Operational Notes

1. NVD is the only source in this project with a direct year-backfill path today.
2. OWASP and PortSwigger are bundled as curated reference records first, not as massive mirrors.
3. The project should expand from reference records to larger corpora only when a normalization rule is verified.
4. All downloads must preserve source URLs and acquisition timestamps.

## Recommended Next Downloads

- Full NVD historical backfill.
- Selected CWE snapshots aligned with the weaknesses already mapped in the project.
- Dated KEV snapshots.
- Historical OWASP Top Ten editions that are publicly available and relevant.