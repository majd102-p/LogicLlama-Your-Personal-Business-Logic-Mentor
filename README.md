# LogicLlama: Offensive Security Reasoning Engine

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue)](https://www.python.org/downloads/)
[![Code Tests](https://img.shields.io/badge/tests-52%2F52-brightgreen)]()
[![Neo4j 5.15+](https://img.shields.io/badge/neo4j-5.15+-green)](https://neo4j.com/)

## Overview

**LogicLlama** is a specialized security reasoning engine designed to identify and analyze **business logic vulnerabilities** — a critical but often overlooked class of security flaws that traditional vulnerability scanners miss.

### What Makes LogicLlama Different?

Instead of asking *"What payload breaks this endpoint?"*, LogicLlama asks:
- *"What intended state transition can be abused?"*
- *"What economic rule can be exploited?"*
- *"What trust assumption is implicit and broken?"*
- *"What workflow dependency can be weaponized?"*

### Core Philosophy

LogicLlama models applications as:
- **State machines** with defined transitions and constraints
- **Economic systems** with costs, flows, and balances
- **Permission graphs** with trust relationships and hierarchies
- **Temporal workflows** with dependencies and sequencing rules

---

## UML & Relationship Model

This section documents the core relationships in a compact UML-style format so contributors can quickly understand how the system fits together.

### Component Diagram

```mermaid
flowchart TB
    User[User / Analyst] --> UI[Streamlit UI]
    User --> CLI[CLI Commands]
    User --> API[FastAPI Layer]

    UI --> Orchestrator[Reasoning Orchestrator]
    CLI --> Orchestrator
    API --> Orchestrator

    Orchestrator --> Ingestion[Ingestion Pipeline]
    Orchestrator --> Storage[SQLite Storage]
    Orchestrator --> Graph[Graph Builder]
    Orchestrator --> Persist[Neo4j Persistence]
    Orchestrator --> RAG[RAG Search]

    Ingestion --> Adapters[Public Source Adapters]
    Adapters --> Sources[NVD / CWE / KEV / OWASP / PortSwigger]
    Graph --> Cases[Logic Cases]
    Persist --> Neo4j[(Neo4j)]
    Storage --> SQLite[(SQLite)]
    RAG --> Vector[(ChromaDB)]
```

### Class Relationship View

```mermaid
classDiagram
    class LogicCase {
        +case_id
        +cve_id
        +title
        +description
        +severity
        +published_date
    }

    class LogicSource {
        +source_id
        +name
        +url
        +last_updated
        +case_count
    }

    class QueryFilter {
        +source
        +severity_min
        +date_from
        +date_to
        +keywords
        +cwe_ids
    }

    class StorageManager {
        +save_case()
        +get_case()
        +query_cases()
        +get_statistics()
    }

    class GraphBuilder {
        +build_graph()
        +compute_similarity()
        +link_cases()
    }

    class Neo4jGraphStore {
        +persist_graph()
        +query_cypher()
        +get_neighbors()
    }

    class LogicIngestionPipeline {
        +run()
        +normalize_sources()
        +validate_records()
    }

    LogicSource "1" --> "many" LogicCase : provides
    QueryFilter ..> LogicCase : filters
    LogicIngestionPipeline ..> LogicSource : consumes
    LogicIngestionPipeline ..> StorageManager : loads
    StorageManager ..> LogicCase : stores
    GraphBuilder ..> LogicCase : analyzes
    GraphBuilder ..> Neo4jGraphStore : exports
    Neo4jGraphStore ..> LogicCase : persists
```

### Sequence Diagram

```mermaid
sequenceDiagram
    actor User
    participant UI as UI / CLI
    participant Pipeline as Ingestion Pipeline
    participant Store as SQLite Storage
    participant Builder as Graph Builder
    participant Graph as Neo4j Store

    User->>UI: Request analysis or ingest data
    UI->>Pipeline: Load and normalize sources
    Pipeline->>Store: Save validated cases
    Store-->>Pipeline: Confirmation
    UI->>Builder: Build or refresh relationships
    Builder->>Store: Read normalized cases
    Builder->>Graph: Persist similarity edges
    Graph-->>UI: Graph ready for querying
```

### Why this matters

- The ingestion layer owns the flow from public sources into normalized cases.
- The storage layer persists canonical records and keeps the system reproducible.
- The graph layer derives relationships and makes cross-case reasoning possible.
- The UI, CLI, and API are thin entry points that should not own domain logic.

---

## Key Features

✅ **21,995+ Curated Security Cases**
- 19,436 CVE records (1999-2025, 27 years of history)
- 1,587 CISA Known Exploited Vulnerabilities
- 969 MITRE CWE weakness classifications
- 6 OWASP Top 10 editions with CWE mappings
- Curated business logic attack patterns from PortSwigger

✅ **Production-Ready Infrastructure**
- SQLite-based persistence with referential integrity
- Neo4j graph database for relationship analysis (optional)
- 38,700+ cross-case similarity edges
- CLI with 18 specialized commands
- Streamlit UI for interactive browsing

✅ **Comprehensive Data Pipeline**
- Automated NVD ingestion and backfill (1999-2025)
- CWE versioning with 8 snapshot archives
- KEV historical snapshots
- OWASP Top 10 curation with temporal tracking
- Live sync capabilities for public sources

✅ **Testing & Validation**
- 52/52 passing tests across all modules
- 100% test coverage for core functionality
- Data validation with Pydantic
- Schema auditing and coverage reporting

✅ **Export & Integration**
- Training corpus: 38,570+ annotated examples
- Simulation corpus: 38,567+ attack scenarios
- Graph export for advanced reasoning
- REST API ready (FastAPI configured)

---

## Quick Start

### Prerequisites
- Python 3.8+
- 4GB RAM minimum (8GB+ recommended)
- 500MB disk space (2GB+ with Neo4j)
- Neo4j 5.15+ (optional but recommended)

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/logicllama.git
   cd logicllama
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Initialize database**
   ```bash
   python -m src.core.cli ingest-fixtures
   ```

5. **Run tests**
   ```bash
   pytest -v
   ```

6. **Launch UI**
   ```bash
   streamlit run src/ui/app.py
   ```

### Docker Setup (Recommended for Production)

```bash
# Start Neo4j
docker run -d \
  -p 7474:7474 -p 7687:7687 \
  -e NEO4J_AUTH=neo4j/password \
  neo4j:5.15

# Configure connection
export NEO4J_URI="bolt://localhost:7687"
export NEO4J_AUTH="neo4j/password"

# Run application
python -m src.core.cli graph-persist
```

---

## CLI Commands

### Data Ingestion
```bash
python -m src.core.cli ingest-fixtures      # Load fixture data
python -m src.core.cli sync                 # Sync public sources
python -m src.core.cli sync-history         # Sync historical data
python -m src.core.cli refresh-all          # Full refresh
```

### Search & Analysis
```bash
python -m src.core.cli search --query "SQL Injection" --limit 10
python -m src.core.cli list --source nvd --limit 20
python -m src.core.cli report --analysis vulnerability-types
python -m src.core.cli audit                # Schema validation
```

### Graph Operations
```bash
python -m src.core.cli export-schema
python -m src.core.cli export-training-corpus
python -m src.core.cli export-simulation-corpus
python -m src.core.cli graph-persist        # Persist to Neo4j
python -m src.core.cli graph-query "MATCH (n) RETURN count(n)"
python -m src.core.cli graph-stats
```

---

## Project Structure

```
logicllama/
├── src/
│   ├── core/                    # Core modules (14 files)
│   │   ├── models.py            # Pydantic domain models
│   │   ├── storage.py           # SQLite persistence layer
│   │   ├── graph.py             # Graph data structures
│   │   ├── graph_builder.py     # Graph construction
│   │   ├── graph_persistence.py # Neo4j integration
│   │   ├── cli.py               # CLI command implementations
│   │   ├── master_schema.py     # AI reasoning schema
│   │   ├── training_corpus.py   # Export training data
│   │   ├── simulation_corpus.py # Export scenarios
│   │   ├── settings.py          # Configuration management
│   │   ├── audit.py             # Schema validation
│   │   ├── reporting.py         # Analytics & reports
│   │   └── ...
│   │
│   ├── ingestion/               # Data pipeline (7 files)
│   │   ├── adapters.py          # Source adapters
│   │   ├── pipeline.py          # Pipeline orchestration
│   │   ├── sync.py              # Live sync service
│   │   ├── archive_cwe_snapshots.py
│   │   ├── archive_kev_snapshots.py
│   │   ├── curate_owasp_editions.py
│   │   └── __init__.py
│   │
│   ├── rag/                     # Retrieval-augmented search
│   │   └── search.py
│   │
│   └── ui/                      # User interface
│       └── app.py               # Streamlit application
│
├── tests/                       # Test suite (7 files)
│   ├── test_cli.py
│   ├── test_ingestion_pipeline.py
│   ├── test_graph_persistence.py
│   ├── test_master_schema.py
│   ├── test_public_source_adapters.py
│   ├── test_source_sync.py
│   └── test_exporters.py
│
├── data/
│   ├── cve_database/           # NVD data
│   ├── fixtures/               # Reference data (OWASP, CWE, KEV, PortSwigger)
│   └── logic_bugs/             # Business logic cases (extensible)
│
├── docs/                       # Comprehensive documentation
│   ├── IMPLEMENTATION_GUIDE.md
│   ├── DATA_SOURCES.md
│   ├── MASTER_SCHEMA.json
│   ├── SOURCE_MANIFEST.json
│   └── ...
│
├── database/
│   └── logicllama.sqlite3     # Main database (21,995 records)
│
├── requirements.txt            # Python dependencies
├── README.md                   # This file
├── CONTRIBUTING.md             # Contribution guidelines
├── ARCHITECTURE.md             # Technical architecture
├── DEVELOPMENT.md              # Development setup
├── LICENSE                     # MIT License
└── .github/
    ├── workflows/
    │   ├── tests.yml           # CI/CD pipeline
    │   └── publish.yml         # Release automation
    └── ISSUE_TEMPLATE/
        ├── bug_report.md
        └── feature_request.md
```

---

## Data Sources

| Source | Coverage | Records | Status |
|--------|----------|---------|--------|
| **NVD** | 1999-2025 (27 years) | 19,436 CVEs | ✅ Complete |
| **MITRE CWE** | v4.9 - v4.20 (8 versions) | 969 weaknesses | ✅ Complete |
| **CISA KEV** | Historical snapshots | 1,587 entries | ✅ Complete |
| **OWASP Top 10** | 2007, 2010, 2013, 2017, 2021, 2025 | 6 editions | ✅ Complete |
| **PortSwigger** | Access Control & Business Logic | 2 guides | ✅ Complete |

**Total Curated Cases**: 21,995 security cases with cross-referenced relationships

---

## Architecture Highlights

### Modular Design
- **Separation of Concerns**: Data ingestion, persistence, API, and UI layers are independent
- **Extensible Adapters**: Add new data sources by implementing `SourceAdapter` interface
- **Plugin-Ready**: Graph operations can run with or without Neo4j

### Data Pipeline
```
Public Sources (NVD, CWE, KEV, OWASP, PortSwigger)
    ↓
Adapters (normalize & extract)
    ↓
SQLite Storage (21,995 cases)
    ↓
Graph Builder (compute relationships)
    ↓
Neo4j Export (optional, for advanced queries)
    ↓
CLI / UI / API (consumption layer)
```

### Graph Database
- **38,700+ edges** representing cross-case similarity
- **Efficient querying** for multi-hop relationships
- **Optional but recommended** for complex reasoning workflows
- **Fully reversible** (can always rebuild from SQLite)

---

## Development

### Setup Development Environment
```bash
# Clone and install
git clone https://github.com/yourusername/logicllama.git
cd logicllama
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Install dev dependencies
pip install pytest pytest-cov black flake8 mypy

# Run tests
pytest -v --cov=src

# Format code
black src/

# Lint
flake8 src/ --max-line-length=100

# Type checking
mypy src/
```

### Testing
```bash
# Run all tests
pytest

# Run specific test module
pytest tests/test_cli.py -v

# Generate coverage report
pytest --cov=src --cov-report=html

# Run with markers
pytest -m "not slow"
```

### Building & Documentation
```bash
# Generate API docs
python -m src.core.cli export-schema

# Export datasets
python -m src.core.cli export-training-corpus --output training.json
python -m src.core.cli export-simulation-corpus --output scenarios.json
```

---

## Contributing

We welcome contributions! Please see [CONTRIBUTING.md](./CONTRIBUTING.md) for detailed guidelines.

### Quick Contribution Steps
1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass (`pytest`)
6. Format code (`black src/`)
7. Commit with clear messages (`git commit -m 'Add amazing feature'`)
8. Push to branch (`git push origin feature/amazing-feature`)
9. Open a Pull Request

### Contribution Areas
- 🐛 **Bug Fixes**: Found an issue? Open a PR
- ✨ **Features**: New adapters, UI improvements, analysis tools
- 📚 **Documentation**: Improve docs, add examples, create guides
- 🧪 **Tests**: Increase coverage, add edge cases
- ⚡ **Performance**: Optimize queries, improve algorithms

---

## Technology Stack

### Backend
- **Language**: Python 3.8+
- **Database**: SQLite (primary), Neo4j 5.15+ (optional)
- **Validation**: Pydantic 2.5.2
- **Testing**: pytest 7.4.3
- **Task Queue**: Celery (ready for integration)

### Frontend
- **UI Framework**: Streamlit
- **API**: FastAPI (configured)
- **Web Server**: Uvicorn

### AI/ML (Optional)
- **LLM Framework**: LangChain
- **Local Inference**: Ollama
- **Vector Database**: ChromaDB
- **Embeddings**: Configurable (sentence-transformers, OpenAI, etc.)

### DevOps
- **Containerization**: Docker, docker-compose
- **CI/CD**: GitHub Actions
- **Code Quality**: Black, flake8, mypy
- **Monitoring**: Standard logging with configurable levels

---

## Roadmap

### Phase 1: Core (✅ Complete)
- [x] Data ingestion pipeline
- [x] SQLite persistence
- [x] Neo4j integration
- [x] CLI interface
- [x] Comprehensive testing

### Phase 2: UI & Analytics (In Progress)
- [ ] Streamlit dashboard enhancements
- [ ] Advanced filtering & visualization
- [ ] Case relationship explorer
- [ ] Export report generation

### Phase 3: AI Integration (Planned)
- [ ] LLM-based case reasoning
- [ ] Vector search optimization
- [ ] Automated pattern detection
- [ ] Insight generation

### Phase 4: Production & Scaling (Planned)
- [ ] REST API endpoints
- [ ] Docker deployment
- [ ] CI/CD pipelines
- [ ] Performance monitoring
- [ ] Scheduled data updates

---

## Performance Metrics

| Metric | Current | Target |
|--------|---------|--------|
| Search Speed | <500ms | <200ms |
| Database Size | 21,995 cases | Scalable to 100k+ |
| Test Coverage | 100% (core) | >95% (all modules) |
| Build Time | ~2 minutes | <1 minute |
| Memory Usage | <500MB (baseline) | Optimize as needed |

---

## Troubleshooting

### Database Not Found
```bash
# Reinitialize database
python -m src.core.cli ingest-fixtures
```

### Neo4j Connection Failed
```bash
# Check Neo4j is running
docker ps | grep neo4j

# Test connection
python -c "from src.core.graph_persistence import GraphPersistence; print(GraphPersistence().health_check())"
```

### Tests Failing
```bash
# Run with verbose output
pytest -vv -s

# Check environment variables
echo $PYTHONPATH
echo $NEO4J_URI

# Clear cache
rm -rf .pytest_cache __pycache__
```

### Performance Issues
```bash
# Check database integrity
sqlite3 database/logicllama.sqlite3 "PRAGMA integrity_check;"

# Analyze query performance
python -m src.core.cli graph-stats
```

---

## License

This project is licensed under the MIT License - see [LICENSE](./LICENSE) file for details.

---

## Citation

If you use LogicLlama in your research or work, please cite:

```bibtex
@software{logicllama2026,
  title={LogicLlama: Offensive Security Reasoning Engine},
  author={Your Name},
  year={2026},
  url={https://github.com/yourusername/logicllama}
}
```

---

## Contact & Community

- **Issues & Bugs**: [GitHub Issues](https://github.com/yourusername/logicllama/issues)
- **Discussions**: [GitHub Discussions](https://github.com/yourusername/logicllama/discussions)
- **Security**: [SECURITY.md](./SECURITY.md) for responsible disclosure

---

## Acknowledgments

- NIST for NVD data and standards
- MITRE for CWE taxonomy
- CISA for KEV catalog
- OWASP for Top 10 guidance
- PortSwigger for security insights
- Community contributors and maintainers

---

**Last Updated**: May 9, 2026  
**Status**: Production Ready ✅  
**Current Version**: 1.0.0
