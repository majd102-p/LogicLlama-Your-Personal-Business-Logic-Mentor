"""Command-line entrypoint for LogicLlama maintenance tasks."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from src.core.settings import get_settings
from src.core.audit import build_project_audit
from src.core.schema_projection import build_master_schema_projection
from src.core.reporting import build_store_report
from src.core.storage import SQLiteLogicStore
from src.core.graph import GraphQuery, GraphRelationType, GraphNodeType
from src.core.graph_builder import GraphBuilder
from src.core.training_corpus import TrainingCorpusExporter
from src.core.simulation_corpus import SimulationCorpusExporter
from src.core.graph_linkage import build_cross_case_edges, export_to_networkx
from src.ingestion import PublicSourceSyncService, ingest_fixture_directory
from src.rag import LogicSearchService


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="logicllama", description="LogicLlama local workflow commands")
    subparsers = parser.add_subparsers(dest="command", required=True)

    ingest_parser = subparsers.add_parser("ingest-fixtures", help="Load JSON fixtures from the local fixture directory")
    ingest_parser.add_argument("--directory", type=Path, default=None, help="Override fixture directory")

    sync_parser = subparsers.add_parser("sync", help="Sync public source feeds into SQLite")
    sync_parser.add_argument("--nvd-limit", type=int, default=25)
    sync_parser.add_argument("--nvd-year", type=int, default=None, help="Optional year filter for NVD sync")
    sync_parser.add_argument("--cwe-limit", type=int, default=100)
    sync_parser.add_argument("--skip-nvd", action="store_true")
    sync_parser.add_argument("--skip-kev", action="store_true")
    sync_parser.add_argument("--skip-cwe", action="store_true")

    sync_history_parser = subparsers.add_parser("sync-history", help="Backfill historical NVD records into SQLite")
    sync_history_parser.add_argument("--start-year", type=int, default=1999)
    sync_history_parser.add_argument("--end-year", type=int, default=None)

    refresh_parser = subparsers.add_parser("refresh-all", help="Run full local data refresh (fixtures, sync, history, archives)")
    refresh_parser.add_argument("--nvd-limit", type=int, default=25)
    refresh_parser.add_argument("--cwe-limit", type=int, default=100)
    refresh_parser.add_argument("--history-start-year", type=int, default=1999)
    refresh_parser.add_argument("--history-end-year", type=int, default=None)
    refresh_parser.add_argument("--skip-history", action="store_true")
    refresh_parser.add_argument("--skip-archives", action="store_true")

    search_parser = subparsers.add_parser("search", help="Search normalized cases")
    search_parser.add_argument("query", nargs="?", default="")
    search_parser.add_argument("--limit", type=int, default=10)

    list_parser = subparsers.add_parser("list", help="List stored cases")
    list_parser.add_argument("--limit", type=int, default=10)

    report_parser = subparsers.add_parser("report", help="Export a summary of the current store")
    report_parser.add_argument("--limit", type=int, default=10, help="Number of recent sources to include")
    report_parser.add_argument("--output", type=Path, default=None, help="Write the summary to a file instead of stdout")
    report_parser.add_argument("--format", choices=["json", "text", "csv"], default="json", help="Output format")

    audit_parser = subparsers.add_parser("audit", help="Compare docs-driven schema goals with the current implementation")
    audit_parser.add_argument("--output", type=Path, default=None, help="Write the audit to a file instead of stdout")
    audit_parser.add_argument("--format", choices=["json", "text"], default="text", help="Output format")

    export_parser = subparsers.add_parser("export-schema", help="Export a stored case as a MASTER_SCHEMA-shaped projection")
    export_parser.add_argument("pattern_id", help="Case pattern identifier to export")
    export_parser.add_argument("--output", type=Path, default=None, help="Write the export to a file instead of stdout")
    export_parser.add_argument("--format", choices=["json", "text"], default="json", help="Output format")

    graph_parser = subparsers.add_parser("graph-query", help="Query the knowledge graph for case relationships")
    graph_parser.add_argument("pattern_id", help="Case pattern identifier to start from")
    graph_parser.add_argument("--depth", type=int, default=2, help="Maximum traversal depth (1-4)")
    graph_parser.add_argument("--relation-type", type=str, default=None, help="Filter by relation type (e.g., maps_to, derived_from)")
    graph_parser.add_argument("--node-type", type=str, default=None, help="Filter by node type (e.g., cwe, signal, source)")
    graph_parser.add_argument("--rebuild", action="store_true", help="Rebuild entire graph before querying (slow, use for full refresh)")
    graph_parser.add_argument("--output", type=Path, default=None, help="Write the export to a file instead of stdout")
    graph_parser.add_argument("--format", choices=["json", "text"], default="json", help="Output format")

    training_parser = subparsers.add_parser("export-training-corpus", help="Export training Q&A pairs from all cases")
    training_parser.add_argument("--output", type=Path, default=None, help="Write to file instead of stdout")
    training_parser.add_argument("--format", choices=["json", "jsonl"], default="jsonl", help="Output format")
    training_parser.add_argument("--limit", type=int, default=None, help="Limit number of cases to include")

    simulation_parser = subparsers.add_parser("export-simulation-corpus", help="Export simulation test cases from all cases")
    simulation_parser.add_argument("--output", type=Path, default=None, help="Write to file instead of stdout")
    simulation_parser.add_argument("--format", choices=["json", "jsonl"], default="jsonl", help="Output format")
    simulation_parser.add_argument("--limit", type=int, default=None, help="Limit number of cases to include")

    export_graph_parser = subparsers.add_parser("export-graph", help="Export full knowledge graph with cross-case linkage")
    export_graph_parser.add_argument("--output", type=Path, default=None, help="Write to file instead of stdout")
    export_graph_parser.add_argument("--format", choices=["json", "networkx"], default="json", help="Output format")
    export_graph_parser.add_argument("--similarity-threshold", type=float, default=0.3, help="Threshold for linking similar cases (0.0-1.0)")
    export_graph_parser.add_argument("--limit", type=int, default=None, help="Limit number of cases to include in graph")

    graph_persist_parser = subparsers.add_parser("graph-persist", help="Initialize Neo4j graph database")
    graph_persist_parser.add_argument("--uri", default=None, help="Neo4j URI (default: $NEO4J_URI or bolt://localhost:7687)")
    graph_persist_parser.add_argument("--username", default=None, help="Neo4j username (default: $NEO4J_USERNAME or neo4j)")
    graph_persist_parser.add_argument("--password", default=None, help="Neo4j password (default: $NEO4J_PASSWORD or password)")
    graph_persist_parser.add_argument("--database", default=None, help="Neo4j database name (default: $NEO4J_DATABASE or neo4j)")
    graph_persist_parser.add_argument("--verify-ssl", action="store_true", default=True, help="Verify SSL certificates")

    graph_sync_parser = subparsers.add_parser("graph-sync", help="Sync all cases and relationships to Neo4j")
    graph_sync_parser.add_argument("--uri", default=None, help="Neo4j URI (default: $NEO4J_URI or bolt://localhost:7687)")
    graph_sync_parser.add_argument("--username", default=None, help="Neo4j username (default: $NEO4J_USERNAME or neo4j)")
    graph_sync_parser.add_argument("--password", default=None, help="Neo4j password (default: $NEO4J_PASSWORD or password)")
    graph_sync_parser.add_argument("--database", default=None, help="Neo4j database name (default: $NEO4J_DATABASE or neo4j)")
    graph_sync_parser.add_argument("--verify-ssl", action="store_true", default=True, help="Verify SSL certificates")
    graph_sync_parser.add_argument("--limit", type=int, default=None, help="Limit number of cases to sync")

    graph_query_parser = subparsers.add_parser("graph-search", help="Query Neo4j for similar cases or CWE mappings")
    graph_query_parser.add_argument("--query-type", choices=["similar", "cwe", "focus"], default="similar", help="Query type")
    graph_query_parser.add_argument("--pattern-id", help="Pattern ID for similar cases query")
    graph_query_parser.add_argument("--cwe-id", help="CWE ID for CWE query")
    graph_query_parser.add_argument("--focus", help="Focus area for focus cluster query")
    graph_query_parser.add_argument("--limit", type=int, default=10, help="Result limit")
    graph_query_parser.add_argument("--uri", default=None, help="Neo4j URI")
    graph_query_parser.add_argument("--username", default=None, help="Neo4j username")
    graph_query_parser.add_argument("--password", default=None, help="Neo4j password")
    graph_query_parser.add_argument("--database", default=None, help="Neo4j database name")
    graph_query_parser.add_argument("--format", choices=["json", "text"], default="text", help="Output format")

    graph_stats_parser = subparsers.add_parser("graph-stats", help="Show Neo4j graph statistics")
    graph_stats_parser.add_argument("--uri", default=None, help="Neo4j URI")
    graph_stats_parser.add_argument("--username", default=None, help="Neo4j username")
    graph_stats_parser.add_argument("--password", default=None, help="Neo4j password")
    graph_stats_parser.add_argument("--database", default=None, help="Neo4j database name")
    graph_stats_parser.add_argument("--format", choices=["json", "text"], default="text", help="Output format")

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    settings = get_settings()
    store = SQLiteLogicStore(settings.database_path)
    store.initialize()

    if args.command == "ingest-fixtures":
        directory = args.directory or settings.fixture_dir
        report = ingest_fixture_directory(store, directory)
        print(f"ingested fixtures: files={report.files_seen} sources={report.sources_written} cases={report.cases_written}")
        return 0

    if args.command == "sync":
        service = PublicSourceSyncService(store)
        reports = []
        if not args.skip_nvd:
            if args.nvd_year is not None:
                reports.append(service.sync_nvd_year(year=args.nvd_year, limit=args.nvd_limit))
            else:
                reports.append(service.sync_nvd(limit=args.nvd_limit))
        if not args.skip_kev:
            reports.append(service.sync_kev())
        if not args.skip_cwe:
            reports.append(service.sync_cwe(limit=args.cwe_limit))
        for report in reports:
            print(f"{report.source_name}: fetched={report.records_fetched} ingested={report.records_ingested}")
        return 0

    if args.command == "sync-history":
        service = PublicSourceSyncService(store)
        report = service.sync_nvd_history(start_year=args.start_year, end_year=args.end_year)
        print(f"{report.source_name}: fetched={report.records_fetched} ingested={report.records_ingested}")
        return 0

    if args.command == "refresh-all":
        fixture_report = ingest_fixture_directory(store, settings.fixture_dir)
        print(
            f"fixtures: files={fixture_report.files_seen} "
            f"sources={fixture_report.sources_written} cases={fixture_report.cases_written}"
        )

        service = PublicSourceSyncService(store)
        reports = [
            service.sync_nvd(limit=args.nvd_limit),
            service.sync_kev(),
            service.sync_cwe(limit=args.cwe_limit),
        ]
        if not args.skip_history:
            reports.append(
                service.sync_nvd_history(
                    start_year=args.history_start_year,
                    end_year=args.history_end_year,
                )
            )

        for report in reports:
            print(f"{report.source_name}: fetched={report.records_fetched} ingested={report.records_ingested}")

        if not args.skip_archives:
            from src.ingestion import archive_cwe_snapshots, archive_kev_snapshots, curate_owasp_editions

            cwe_result = archive_cwe_snapshots.run_archive(settings.fixture_dir / "cwe_snapshots")
            kev_result = archive_kev_snapshots.run_archive(settings.fixture_dir / "kev_snapshots")
            owasp_result = curate_owasp_editions.run_curation(settings.fixture_dir / "owasp_editions")

            print(f"cwe-archive: downloaded={cwe_result['downloaded']}/{cwe_result['total']}")
            print(f"kev-archive: downloaded={kev_result['downloaded']}/{kev_result['total']}")
            print(f"owasp-editions: created={owasp_result['created']}/{owasp_result['total']}")

        return 0

    if args.command == "search":
        search_service = LogicSearchService(store)
        results = search_service.search(args.query or None, limit=args.limit)
        for logic_case in results:
            print(f"{logic_case.pattern_id} | {logic_case.title} | {logic_case.focus} | {logic_case.confidence:.2f}")
        return 0

    if args.command == "list":
        for logic_case in store.list_cases(limit=args.limit):
            print(f"{logic_case.pattern_id} | {logic_case.title} | {logic_case.source_type.value}")
        return 0

    if args.command == "report":
        report = build_store_report(store, limit=args.limit)
        if args.format == "text":
            payload = report.to_text()
        elif args.format == "csv":
            payload = report.to_csv()
        else:
            payload = json.dumps(report.to_dict(), indent=2, ensure_ascii=True)
        if args.output is not None:
            args.output.write_text(payload, encoding="utf-8")
        else:
            print(payload)
        return 0

    if args.command == "audit":
        report = build_project_audit(settings.project_root)
        if args.format == "text":
            payload = report.to_text()
        else:
            payload = json.dumps(report.to_dict(), indent=2, ensure_ascii=True)
        if args.output is not None:
            args.output.write_text(payload, encoding="utf-8")
        else:
            print(payload)
        return 0

    if args.command == "export-schema":
        logic_case = store.get_case(args.pattern_id)
        if logic_case is None:
            parser.error(f"Unknown pattern_id: {args.pattern_id}")
        source = store.get_source(logic_case.source_ids[0]) if logic_case.source_ids else None
        projection = build_master_schema_projection(logic_case, source=source)
        if args.format == "json":
            payload = json.dumps(projection, indent=2, ensure_ascii=True)
        else:
            payload = (
                f"pattern_id: {projection['pattern_id']}\n"
                f"focus: {projection['focus']}\n"
                f"title: {projection['title']}\n"
                f"source_type: {projection['metadata'].get('source_type', 'unknown')}\n"
                f"covered_fields: {', '.join(sorted(projection.keys()))}"
            )
        if args.output is not None:
            args.output.write_text(payload, encoding="utf-8")
        else:
            print(payload)
        return 0

    if args.command == "graph-query":
        # Optionally rebuild entire graph
        builder = GraphBuilder(store)
        if args.rebuild:
            synced = builder.sync_all_cases()
        else:
            # Only sync the specific case and related cases
            case = store.get_case(args.pattern_id)
            if case:
                builder.sync_case_graph(case)
                # Also sync cases related via source_ids or cwe_ids
                for source_id in case.source_ids:
                    for related_case in store.list_cases(limit=100):
                        if source_id in related_case.source_ids:
                            builder.sync_case_graph(related_case)
        
        # Parse relation type filter
        relation_types = None
        if args.relation_type:
            try:
                relation_types = [GraphRelationType(args.relation_type)]
            except ValueError:
                parser.error(f"Unknown relation type: {args.relation_type}")
        
        # Parse node type filter
        node_types = None
        if args.node_type:
            try:
                node_types = [GraphNodeType(args.node_type)]
            except ValueError:
                parser.error(f"Unknown node type: {args.node_type}")
        
        # Execute traversal
        query = GraphQuery(
            start_node_id=args.pattern_id,
            relation_types=relation_types,
            max_depth=min(max(args.depth, 1), 4),
            node_types=node_types,
        )
        result = store.query_graph(query)
        
        if args.format == "json":
            payload = json.dumps(result.to_dict(), indent=2, ensure_ascii=True)
        else:
            lines = [
                f"Graph Query Results",
                f"===================",
                f"Start: {query.start_node_id}",
                f"Depth: {query.max_depth}",
                f"Nodes found: {len(result.nodes)}",
                f"Edges found: {len(result.edges)}",
                f"Traversed: {result.traversed_count}",
                f"",
                f"Nodes:",
            ]
            for node in result.nodes:
                lines.append(f"  {node.node_id} ({node.node_type.value}): {node.label}")
            
            lines.append("")
            lines.append("Edges:")
            for edge in result.edges:
                lines.append(f"  {edge.from_node_id} --[{edge.relation_type.value}]--> {edge.to_node_id}" + (f" (weight: {edge.weight:.2f})" if edge.weight else ""))
            
            payload = "\n".join(lines)
        
        if args.output is not None:
            args.output.write_text(payload, encoding="utf-8")
        else:
            print(payload)
        return 0

    if args.command == "export-training-corpus":
        from src.core.training_corpus import TrainingCorpusExporter

        exporter = TrainingCorpusExporter()
        cases = store.list_cases(limit=args.limit or 10000)
        for case in cases:
            exporter.add_case(case)

        if args.format == "jsonl":
            payload = exporter.to_jsonl()
        else:
            payload = json.dumps(exporter.to_dict(), indent=2, ensure_ascii=True)

        if args.output is not None:
            args.output.write_text(payload, encoding="utf-8")
        else:
            print(payload)
        
        # Print statistics
        stats = exporter.statistics()
        print(f"\nTraining corpus statistics:", file=__import__("sys").stderr)
        print(f"  Total examples: {stats['total_examples']}", file=__import__("sys").stderr)
        return 0

    if args.command == "export-simulation-corpus":
        from src.core.simulation_corpus import SimulationCorpusExporter

        exporter = SimulationCorpusExporter()
        cases = store.list_cases(limit=args.limit or 10000)
        for case in cases:
            exporter.add_case(case)

        if args.format == "jsonl":
            payload = exporter.to_jsonl()
        else:
            payload = json.dumps(exporter.to_dict(), indent=2, ensure_ascii=True)

        if args.output is not None:
            args.output.write_text(payload, encoding="utf-8")
        else:
            print(payload)
        
        # Print statistics
        stats = exporter.statistics()
        print(f"\nSimulation corpus statistics:", file=__import__("sys").stderr)
        print(f"  Total simulations: {stats['total_simulations']}", file=__import__("sys").stderr)
        return 0

    if args.command == "export-graph":
        from src.core.graph_linkage import build_cross_case_edges, export_to_networkx

        # Load all cases and build graph
        builder = GraphBuilder(store)
        cases = store.list_cases(limit=args.limit or 10000)
        for case in cases:
            builder.sync_case_graph(case)

        # Load full graph
        nodes, edges = store.load_graph_for_case(cases[0].pattern_id) if cases else ([], [])
        
        # Add cross-case similarity edges
        cross_case_edges = build_cross_case_edges(cases, similarity_threshold=args.similarity_threshold)
        for edge in cross_case_edges:
            store.upsert_graph_edge(edge)
            edges.append(edge)

        if args.format == "networkx":
            output = export_to_networkx(nodes, edges)
            payload = json.dumps(output, indent=2, ensure_ascii=True, default=str)
        else:
            output = {
                "version": "1.0.0",
                "format": "knowledge_graph",
                "nodes_count": len(nodes),
                "edges_count": len(edges),
                "nodes": [n.to_dict() for n in nodes],
                "edges": [e.to_dict() for e in edges],
            }
            payload = json.dumps(output, indent=2, ensure_ascii=True, default=str)

        if args.output is not None:
            args.output.write_text(payload, encoding="utf-8")
        else:
            print(payload)
        
        print(f"\nGraph export statistics:", file=__import__("sys").stderr)
        print(f"  Nodes: {len(nodes)}", file=__import__("sys").stderr)
        print(f"  Edges: {len(edges)}", file=__import__("sys").stderr)
        return 0

    if args.command == "graph-persist":
        from src.core.graph_persistence import Neo4jGraphStore
        
        # Get Neo4j settings (prefer args, then env, then defaults)
        uri = args.uri or settings.neo4j.uri
        username = args.username or settings.neo4j.username
        password = args.password or settings.neo4j.password
        database = args.database or settings.neo4j.database
        
        graph_store = Neo4jGraphStore(
            uri=uri,
            username=username,
            password=password,
            database=database,
            verify_ssl=args.verify_ssl,
        )
        
        try:
            graph_store.connect()
            graph_store.initialize_schema()
            print(f"Neo4j graph database initialized at {uri}")
            print(f"  - Constraints created")
            print(f"  - Indexes created")
            print(f"  - Ready for graph sync")
            graph_store.disconnect()
            return 0
        except Exception as e:
            print(f"Error initializing Neo4j: {e}", file=__import__("sys").stderr)
            return 1

    if args.command == "graph-sync":
        from src.core.graph_persistence import Neo4jGraphStore
        
        uri = args.uri or settings.neo4j.uri
        username = args.username or settings.neo4j.username
        password = args.password or settings.neo4j.password
        database = args.database or settings.neo4j.database
        
        graph_store = Neo4jGraphStore(
            uri=uri,
            username=username,
            password=password,
            database=database,
            verify_ssl=args.verify_ssl,
        )
        
        try:
            graph_store.connect()
            print(f"Syncing cases to Neo4j at {uri}...")
            
            cases = store.list_cases(limit=args.limit or 10000)
            result = graph_store.sync_all_cases(cases)
            
            print(f"Sync complete:")
            print(f"  Cases synced: {result['cases_synced']}")
            print(f"  Edges created: {result['edges_created']}")
            print(f"  Timestamp: {result['timestamp']}")
            
            graph_store.disconnect()
            return 0
        except Exception as e:
            print(f"Error syncing to Neo4j: {e}", file=__import__("sys").stderr)
            return 1

    if args.command == "graph-search":
        from src.core.graph_persistence import Neo4jGraphStore
        
        uri = args.uri or settings.neo4j.uri
        username = args.username or settings.neo4j.username
        password = args.password or settings.neo4j.password
        database = args.database or settings.neo4j.database
        
        graph_store = Neo4jGraphStore(
            uri=uri,
            username=username,
            password=password,
            database=database,
            verify_ssl=True,
        )
        
        try:
            graph_store.connect()
            
            if args.query_type == "similar":
                if not args.pattern_id:
                    parser.error("--pattern-id required for 'similar' query type")
                results = graph_store.query_similar_cases(args.pattern_id, limit=args.limit)
                title = f"Cases similar to {args.pattern_id}"
            elif args.query_type == "cwe":
                if not args.cwe_id:
                    parser.error("--cwe-id required for 'cwe' query type")
                results = graph_store.query_cwe_cases(args.cwe_id, limit=args.limit)
                title = f"Cases mapping to CWE-{args.cwe_id}"
            else:  # focus
                if not args.focus:
                    parser.error("--focus required for 'focus' query type")
                results = graph_store.query_focus_cluster(args.focus, limit=args.limit)
                title = f"Cases with focus: {args.focus}"
            
            if args.format == "json":
                output = {"query_type": args.query_type, "results": results}
                payload = json.dumps(output, indent=2, ensure_ascii=True)
            else:
                lines = [title, "=" * len(title), ""]
                for result in results:
                    lines.append(f"  {result.get('pattern_id', 'N/A')} | {result.get('title', 'N/A')}")
                    if result.get('similarity'):
                        lines.append(f"    Similarity: {result['similarity']:.2f}")
                    if result.get('relation_type'):
                        lines.append(f"    Relation: {result['relation_type']}")
                    lines.append("")
                payload = "\n".join(lines)
            
            print(payload)
            graph_store.disconnect()
            return 0
        except Exception as e:
            print(f"Error querying Neo4j: {e}", file=__import__("sys").stderr)
            return 1

    if args.command == "graph-stats":
        from src.core.graph_persistence import Neo4jGraphStore
        
        uri = args.uri or settings.neo4j.uri
        username = args.username or settings.neo4j.username
        password = args.password or settings.neo4j.password
        database = args.database or settings.neo4j.database
        
        graph_store = Neo4jGraphStore(
            uri=uri,
            username=username,
            password=password,
            database=database,
            verify_ssl=True,
        )
        
        try:
            graph_store.connect()
            stats = graph_store.get_graph_stats()
            
            if args.format == "json":
                payload = json.dumps(stats, indent=2, ensure_ascii=True)
            else:
                lines = [
                    "Neo4j Graph Statistics",
                    "=======================",
                    "",
                    "Nodes by Type:",
                ]
                for node_type, count in stats.get("nodes_by_type", {}).items():
                    lines.append(f"  {node_type}: {count}")
                
                lines.append("")
                lines.append("Edges by Type:")
                for edge_type, count in stats.get("edges_by_type", {}).items():
                    lines.append(f"  {edge_type}: {count}")
                
                lines.extend([
                    "",
                    f"Total Nodes: {stats.get('total_nodes', 0)}",
                    f"Total Edges: {stats.get('total_edges', 0)}",
                    f"Avg Similarity: {stats.get('avg_similarity', 'N/A')}",
                    f"Timestamp: {stats.get('timestamp', 'N/A')}",
                ])
                payload = "\n".join(lines)
            
            print(payload)
            graph_store.disconnect()
            return 0
        except Exception as e:
            print(f"Error getting graph stats: {e}", file=__import__("sys").stderr)
            return 1

    return 1


if __name__ == "__main__":
    raise SystemExit(main())
