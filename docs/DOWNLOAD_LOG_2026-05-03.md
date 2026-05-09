# Download Log - 2026-05-03

This log records actual data downloads executed for the LogicLlama local store.

## Commands Executed

1. `python -m src.core.cli sync --skip-nvd --cwe-limit 1000`
2. `python -m src.core.cli sync --skip-kev --skip-cwe --nvd-limit 100`
3. `python -m src.core.cli sync --skip-kev --skip-cwe --nvd-year 2025 --nvd-limit 60`
4. `python -m src.core.cli sync --skip-kev --skip-cwe --nvd-year 2024 --nvd-limit 60`
5. `python -m src.core.cli sync --skip-kev --skip-cwe --nvd-year 2023 --nvd-limit 60`

## Results Observed

- KEV: fetched=1587 ingested=1587
- CWE: fetched=969 ingested=969
- NVD (latest batch): fetched=100 ingested=100
- NVD 2025: fetched=60 ingested=60
- NVD 2024: fetched=60 ingested=60
- NVD 2023: fetched=20 ingested=20

## Notes

- NVD can throttle with HTTP 429 during aggressive pagination.
- Year-scoped sync uses monthly windows to avoid invalid wide date ranges.
- Sync logic keeps partial NVD pages instead of failing the entire operation on 429.

## Additional Refresh Run (Later Same Day)

### Commands Executed

1. `python -m src.core.cli ingest-fixtures`
2. `python -m src.core.cli sync --nvd-limit 100 --cwe-limit 1000`
3. `python -m src.core.cli sync --skip-kev --skip-cwe --nvd-year <year> --nvd-limit 60` for all years from 2025 down to 1999
4. `python src/ingestion/archive_cwe_snapshots.py`
5. `python src/ingestion/archive_kev_snapshots.py`
6. `python src/ingestion/curate_owasp_editions.py`
7. `python -m src.core.cli report --format json`

### Results Observed

- Fixture ingest: files=3 sources=3 cases=3
- Live sync:
	- NVD: fetched=100 ingested=100
	- KEV: fetched=1587 ingested=1587
	- CWE: fetched=969 ingested=969
- NVD year loop (2025..1999): all yearly runs completed successfully with fetched/ingested counts between 20 and 60 per year in this pass
- Snapshot archive status:
	- CWE: 8/8 snapshots present and manifest refreshed
	- KEV: current snapshot present; Wayback dated snapshots still unresolved in this run
	- OWASP editions: 6 edition files regenerated and manifest refreshed

### Final Store Summary After Refresh

- case_count: 4682
- source_count: 4680
- cases_by_source_type:
	- cwe: 969
	- kev: 1587
	- nvd: 2123
	- owasp: 1
	- portswigger: 2

### Verification Performed

- `pytest -q`: all tests passed (19 passed)
- JSON validation for docs JSON files: OK