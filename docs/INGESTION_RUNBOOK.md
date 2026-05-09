# LogicLlama Ingestion Runbook

## Purpose

This runbook defines the first release ingestion flow for LogicLlama. The goal is to keep the system local-first, reproducible, and traceable while using only free public sources and curated local fixtures.

## Supported Sources

- NVD CVE API
- MITRE CWE taxonomy snapshots or curated local extractions
- CISA KEV catalog
- OWASP Top 10 derived fixtures
- PortSwigger Web Security Academy derived fixtures
- Local JSON fixtures under `data/fixtures/`

## Canonical Output

Every ingestion path must produce a `LogicSource` and a `LogicCase`.

Required fields:

- Source provenance identifier
- Source family
- Canonical pattern identifier
- Title
- Focus category
- Summary
- Confidence
- Timestamps

## Ingestion Flow

1. Acquire raw source data from a supported public feed or a local fixture.
2. Normalize the raw payload with a source adapter.
3. Validate the normalized source and case with Pydantic models.
4. Persist the result in SQLite.
5. Expose the normalized record through deterministic search and the UI.

## Live Sync Entry Points

- `PublicSourceSyncService.sync_nvd(limit=25)`
- `PublicSourceSyncService.sync_nvd_history(start_year=1999, end_year=None)`
- `PublicSourceSyncService.sync_kev()`
- `PublicSourceSyncService.sync_cwe(limit=100)`
- `PublicSourceSyncService.sync_all(...)`

The first release keeps live sync local and explicit. Run it from a Python shell or a dedicated command layer when you want to refresh the store from public feeds.

## CLI Commands

- `python -m src.core.cli ingest-fixtures`
- `python -m src.core.cli sync --nvd-limit 5 --cwe-limit 10`
- `python -m src.core.cli sync-history --start-year 1999 --end-year 2026`
- `python -m src.core.cli search "forced browsing"`
- `python -m src.core.cli list --limit 10`
- `python -m src.core.cli report --limit 10`
- `python -m src.core.cli report --format text`
- `python -m src.core.cli report --format csv`

The `report` command emits a JSON summary by default. Use `--format text` for a concise human-readable summary or `--format csv` for tabular export. `--output` writes any format to disk.

## Data Handling Rules

- Keep raw payloads in metadata for auditability.
- Do not overwrite source provenance silently.
- Reject malformed or partially mapped records before persistence.
- Prefer deterministic field extraction over heuristic inference in the first release.

## Current Local Fixture Path

- `data/fixtures/portswigger_access_control_reference.json`
- `data/fixtures/portswigger_business_logic_reference.json`
- `data/fixtures/owasp_top_ten_reference.json`

## Source Inventory

The canonical inventory is maintained in [DATA_INVENTORY.md](DATA_INVENTORY.md) and [SOURCE_MANIFEST.json](SOURCE_MANIFEST.json). Use those files when deciding what to sync, what to bundle locally, and what should be treated as a future training corpus.

## Training Posture

The current release is deterministic and does not require a trained model to function. If model training is added later, start with the bundled local references and then expand toward authoritative public corpora that can be normalized reproducibly.

## Historical Coverage

See [HISTORICAL_COVERAGE.md](HISTORICAL_COVERAGE.md) for the year-by-year collection plan and the sources that should be retained over time.

## Execution Logs

Use dated download logs to track real ingestion runs and counts:

- [DOWNLOAD_LOG_2026-05-03.md](DOWNLOAD_LOG_2026-05-03.md)

## Verification Checklist

- Fixture ingestion creates exactly one source and one case.
- Search returns the expected record for a matching query.
- UI bootstraps automatically when the store is empty.
- Tests pass for adapters, ingestion, and retrieval.
