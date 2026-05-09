"""Application settings and filesystem layout for LogicLlama."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class Neo4jSettings:
    """Neo4j connection settings."""

    uri: str
    username: str
    password: str
    database: str
    verify_ssl: bool


@dataclass(frozen=True, slots=True)
class AppSettings:
    """Resolved runtime settings for local-first execution."""

    project_root: Path
    data_dir: Path
    database_path: Path
    fixture_dir: Path
    neo4j: Neo4jSettings


def get_settings() -> AppSettings:
    project_root = Path(__file__).resolve().parents[2]
    data_dir = project_root / "data"
    database_path = Path(os.getenv("LOGICLLAMA_DB_PATH", str(project_root / "database" / "logicllama.sqlite3")))
    fixture_dir = Path(os.getenv("LOGICLLAMA_FIXTURE_DIR", str(data_dir / "fixtures")))
    database_path.parent.mkdir(parents=True, exist_ok=True)
    fixture_dir.mkdir(parents=True, exist_ok=True)

    neo4j_settings = Neo4jSettings(
        uri=os.getenv("NEO4J_URI", "bolt://localhost:7687"),
        username=os.getenv("NEO4J_USERNAME", "neo4j"),
        password=os.getenv("NEO4J_PASSWORD", "password"),
        database=os.getenv("NEO4J_DATABASE", "neo4j"),
        verify_ssl=os.getenv("NEO4J_VERIFY_SSL", "true").lower() == "true",
    )

    return AppSettings(
        project_root=project_root,
        data_dir=data_dir,
        database_path=database_path,
        fixture_dir=fixture_dir,
        neo4j=neo4j_settings,
    )
