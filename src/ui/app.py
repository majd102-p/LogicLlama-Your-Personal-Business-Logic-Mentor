"""Streamlit entrypoint for the first LogicLlama UI."""

from __future__ import annotations

import streamlit as st

from src.core import LogicCase, SQLiteLogicStore, get_settings
from src.core.reporting import build_store_report
from src.ingestion import ingest_fixture_directory
from src.ingestion.sync import PublicSourceSyncService
from src.rag import LogicSearchService


def bootstrap_store() -> SQLiteLogicStore:
    settings = get_settings()
    store = SQLiteLogicStore(settings.database_path)
    store.initialize()
    if not store.list_cases():
        ingest_fixture_directory(store, settings.fixture_dir)
    return store


def render_case(logic_case: LogicCase) -> None:
    st.subheader(logic_case.title)
    st.caption(f"{logic_case.pattern_id} · {logic_case.focus} · {logic_case.status.value}")

    left, right = st.columns(2)
    with left:
        st.markdown("**Summary**")
        st.write(logic_case.summary)
        st.markdown("**Keywords**")
        st.write(", ".join(logic_case.keywords) or "None")
        st.markdown("**CWE IDs**")
        st.write(", ".join(logic_case.cwe_ids) or "None")

    with right:
        st.markdown("**Provenance**")
        st.write(logic_case.source_type.value)
        st.markdown("**Confidence**")
        st.progress(logic_case.confidence)
        st.markdown("**Source IDs**")
        st.write(", ".join(logic_case.source_ids) or "None")

    st.markdown("**Workflow steps**")
    for step in logic_case.workflow_steps:
        st.write(f"{step.order}. {step.title}")

    st.markdown("**Signals**")
    for signal in logic_case.signals:
        st.write(f"{signal.name} = {signal.value} ({signal.confidence:.2f})")

    st.markdown("**Evidence**")
    for evidence in logic_case.evidence:
        st.write(f"{evidence.evidence_id}: {evidence.summary}")


def main() -> None:
    st.set_page_config(page_title="LogicLlama", layout="wide")
    st.title("LogicLlama")
    st.caption("Local-first business logic reasoning workspace")

    store = bootstrap_store()
    search_service = LogicSearchService(store)
    sync_service = PublicSourceSyncService(store)

    st.sidebar.markdown("### Refresh data")
    sync_nvd = st.sidebar.button("Sync NVD")
    sync_kev = st.sidebar.button("Sync KEV")
    sync_cwe = st.sidebar.button("Sync CWE")

    if sync_nvd or sync_kev or sync_cwe:
        with st.spinner("Syncing public sources..."):
            if sync_nvd:
                report = sync_service.sync_nvd(limit=10)
                st.sidebar.success(f"NVD: {report.records_ingested} records ingested")
            if sync_kev:
                report = sync_service.sync_kev()
                st.sidebar.success(f"KEV: {report.records_ingested} records ingested")
            if sync_cwe:
                report = sync_service.sync_cwe(limit=25)
                st.sidebar.success(f"CWE: {report.records_ingested} records ingested")
        st.rerun()

    case_counts = store.count_cases_by_source_type()
    source_counts = store.count_sources_by_source_type()
    report = build_store_report(store, limit=5)

    st.sidebar.markdown("### Provenance")
    for label in sorted(set(case_counts) | set(source_counts)):
        st.sidebar.metric(
            label.upper(),
            case_counts.get(label, 0),
            delta=f"sources {source_counts.get(label, 0)}",
        )

    query = st.sidebar.text_input("Search cases", value="")
    if query.strip():
        cases = search_service.search(query.strip(), limit=25)
    else:
        cases = store.list_cases(limit=25)

    st.sidebar.markdown("**Cases loaded**")
    st.sidebar.write(len(cases))

    st.sidebar.markdown("**Recent sources**")
    for source in store.list_sources(limit=5):
        st.sidebar.write(f"{source.source_type.value} · {source.source_id}")

    st.sidebar.markdown("**Recent sync runs**")
    for sync_run in store.list_sync_runs(limit=5):
        st.sidebar.write(
            f"{sync_run['source_name']} · fetched {sync_run['records_fetched']} · ingested {sync_run['records_ingested']}"
        )

    st.sidebar.download_button(
        "Download store report",
        data=report.to_text(),
        file_name="logicllama-report.txt",
        mime="text/plain",
    )
    st.sidebar.download_button(
        "Download CSV report",
        data=report.to_csv(),
        file_name="logicllama-report.csv",
        mime="text/csv",
    )

    if not cases:
        st.info("No cases available yet. Add fixture JSON files under data/fixtures/ and reload.")
        return

    case_labels = [f"{case.pattern_id} · {case.title}" for case in cases]
    selected_label = st.selectbox("Select a case", options=case_labels)
    selected_case = cases[case_labels.index(selected_label)]
    render_case(selected_case)


if __name__ == "__main__":
    main()
