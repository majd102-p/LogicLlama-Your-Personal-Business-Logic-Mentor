# LogicLlama Architecture

This document describes the technical architecture of LogicLlama, including component organization, data flow, and design patterns.

## Table of Contents

1. [High-Level Overview](#high-level-overview)
2. [Core Modules](#core-modules)
3. [Data Pipeline](#data-pipeline)
4. [Storage Layer](#storage-layer)
5. [Graph Database](#graph-database)
6. [API Layer](#api-layer)
7. [Design Patterns](#design-patterns)
8. [Extension Points](#extension-points)

---

## High-Level Overview

```
┌─────────────────────────────────────────────────────────────┐
│                      User Interfaces                         │
├──────────────────────┬──────────────────┬──────────────────┤
│   Streamlit UI       │   CLI Commands   │   REST API       │
│   (src/ui/app.py)    │  (src/core/cli)  │  (FastAPI ready) │
└──────────────────────┴──────────────────┴──────────────────┘
                              │
┌─────────────────────────────────────────────────────────────┐
│                   Core Reasoning Engine                      │
├──────────────────┬──────────────────┬──────────────────────┤
│  Graph Builder   │  RAG Search      │   Analysis Module   │
│  (graph_builder) │  (rag/search.py) │  (src/analysis/*)   │
└──────────────────┴──────────────────┴──────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────┐
│                  Storage & Persistence                       │
├──────────────────┬────────────────────────────────────────┤
│  SQLite Layer    │        Neo4j Graph Layer (Optional)    │
│  (Primary)       │      (Advanced Reasoning)              │
│  21,995 cases    │      38,700+ edges                     │
└──────────────────┴────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────┐
│                  Data Ingestion Pipeline                     │
├──────────────────────────────────────────────────────────────┤
│ Public Sources → Adapters → Normalization → Storage         │
│ (NVD, CWE, KEV, OWASP, PortSwigger)                         │
└──────────────────────────────────────────────────────────────┘
```

---

## Core Modules

### 1. Models (`src/core/models.py`)

**Purpose**: Define domain entities using Pydantic for validation

**Key Classes**:
```python
class LogicCase(BaseModel):
    """Represents a security case (CVE, KEV, CWE reference, etc.)"""
    case_id: str
    cve_id: Optional[str]
    cwe_ids: List[str]
    title: str
    description: str
    source: str
    severity: Optional[float]
    published_date: Optional[datetime]
    # ... additional fields

class LogicSource(BaseModel):
    """Represents a data source"""
    source_id: str
    name: str
    description: str
    url: str
    last_updated: datetime
    case_count: int
```

---

## Data Pipeline

### Source Flow

```
Public Data Sources
    ↓
Source Adapters (Normalize to LogicCase format)
    ↓
Transformation Layer (Validate & Deduplicate)
    ↓
SQLite Storage Layer (21,995 normalized cases)
    ↓
Graph Construction (38,700+ edges)
    ↓
Neo4j Persistence (Optional)
```

---

## Design Patterns

### 1. Adapter Pattern (Data Ingestion)

Multiple data sources with different formats:
```python
class SourceAdapter(ABC):
    @abstractmethod
    def extract(self) -> List[LogicCase]:
        pass
```

### 2. Repository Pattern (Storage)

Abstract storage implementation:
```python
class StorageManager:
    def save_case(self, case: LogicCase) -> None: pass
    def get_case(self, case_id: str) -> LogicCase: pass
    def query_cases(self, filters) -> List[LogicCase]: pass
```

### 3. Builder Pattern (Graph Construction)

Complex graph creation:
```python
graph = (GraphBuilder()
    .with_similarity_threshold(0.7)
    .with_depth(2)
    .build())
```

### 4. Command Pattern (CLI)

Independent operations:
```bash
python -m src.core.cli search --query "SQL Injection"
python -m src.core.cli graph-persist
```

---

## Performance Characteristics

| Operation | Current | Target |
|-----------|---------|--------|
| Search | <500ms | <200ms |
| Database Size | 21,995 cases | Scalable to 100k+ |
| Graph Query | Sub-second | Milliseconds |
| Test Suite | 52/52 ✅ | 100% coverage |

---

## Extension Points

### Adding a New Data Source

1. Implement `SourceAdapter` interface
2. Register in `src/ingestion/pipeline.py`
3. Add tests
4. Update documentation

### Adding a New CLI Command

1. Define command in `src/core/cli.py`
2. Add tests in `tests/test_cli.py`
3. Document usage
4. Submit PR

### Adding a New Graph Query

1. Define Cypher query
2. Add to `GraphPersistence` class
3. Add tests
4. Document in ARCHITECTURE.md

---

**Document Version**: 1.0  
**Last Updated**: May 9, 2026  
**Status**: Production Ready
