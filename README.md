# LogicLlama
## Autonomous Business Logic Intelligence & Reasoning Platform

> A fully local AI-driven reasoning system designed to analyze, model, and understand business logic vulnerabilities through workflow intelligence, causal inference, adaptive traversal, and graph-native security reasoning.

---

# Vision

LogicLlama is not a traditional vulnerability scanner.  
It is not a wrapper around a language model.  
It is not a payload recommendation chatbot.

LogicLlama is an **Offensive Security Reasoning Engine** focused on one of the hardest unsolved domains in application security.

The current validated runtime covers local ingestion, corpus export, graph traversal, Neo4j persistence, and CLI workflows; deeper autonomous layers remain on the roadmap.

The long-term goal is to model and reason about:

## Business Logic Vulnerabilities

Traditional tooling operates at the request level.  
LogicLlama operates at the workflow level.

Instead of asking:

> “What payload breaks this endpoint?”

LogicLlama asks:

> “What intended state transition, economic rule, trust assumption, or workflow dependency can be abused?”

The platform models applications as:

- State machines
- Economic systems
- Permission graphs
- Temporal workflows
- Causal dependency chains

---

# The Paradigm Shift

Traditional security scanners focus on:

- Static payloads
- Signature matching
- Isolated endpoint analysis
- Single-request testing

Business logic vulnerabilities are fundamentally different.

They are:

- Workflow abuses
- State machine violations
- Economic manipulation paths
- Temporal inconsistencies
- Trust-boundary failures

LogicLlama transforms offensive security from payload execution into reasoning-driven workflow intelligence.

---

# Core Philosophy

Applications are not collections of endpoints.

They are:

- Stateful systems
- Workflow engines
- Economic environments
- Permission graphs
- Temporal processes

LogicLlama continuously:

1. Reconstructs workflows
2. Maps state transitions
3. Generates attack hypotheses
4. Correlates behavioral signals
5. Dynamically adjusts confidence
6. Traverses attack branches
7. Builds explainable evidence graphs

---

# UML & Relationship Model

This section shows how the main components relate to each other in a concise UML-style view.

## Component Diagram

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

## Class Relationships

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

## Sequence View

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

## Why This Matters

- The ingestion layer owns the flow from public sources into normalized cases.
- The storage layer persists canonical records and keeps the system reproducible.
- The graph layer derives relationships and makes cross-case reasoning possible.
- The UI, CLI, and API are thin entry points and should stay free of domain logic.

For the current source inventory and bundled public references, see [docs/DATA_INVENTORY.md](docs/DATA_INVENTORY.md) and [docs/SOURCE_MANIFEST.json](docs/SOURCE_MANIFEST.json).
For the historical collection plan and year-by-year coverage goals, see [docs/HISTORICAL_COVERAGE.md](docs/HISTORICAL_COVERAGE.md).

## Current Operational Quick Start

Use the existing local CLI and UI entrypoints in this repository:

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

Load bundled reference records:

```bash
python -m src.core.cli ingest-fixtures
```

Sync live public feeds:

```bash
python -m src.core.cli sync --nvd-limit 25 --cwe-limit 100
```

Generate a local inventory report:

```bash
python -m src.core.cli report --format text --limit 10
```

Inspect schema and tool-mapping coverage:

```bash
python -m src.core.cli audit --format text
```

Export a schema-shaped case projection:

```bash
python -m src.core.cli export-schema LOGIC-ACCESS-001 --format json
```

Query the knowledge graph for case relationships:

```bash
# Show direct relationships (depth 2, efficient)
python -m src.core.cli graph-query LOGIC-ACCESS-001 --depth 2 --format text

# Show only CWE mappings
python -m src.core.cli graph-query LOGIC-ACCESS-001 --relation-type maps_to --format json

# Show only source derivations
python -m src.core.cli graph-query LOGIC-ACCESS-001 --relation-type derived_from --format text

# Rebuild entire graph (use --rebuild sparingly; it syncs all cases)
python -m src.core.cli graph-query LOGIC-ACCESS-001 --rebuild --depth 3 --format json
```

Export training corpus (Q&A pairs for model training):

```bash
# JSONL format (one example per line)
python -m src.core.cli export-training-corpus --format jsonl --output training.jsonl

# JSON format with metadata
python -m src.core.cli export-training-corpus --format json --limit 100 > training.json
```

Export simulation corpus (test scenarios and attack vectors):

```bash
# JSONL format (one simulation per line)
python -m src.core.cli export-simulation-corpus --format jsonl --output simulations.jsonl

# JSON format with statistics
python -m src.core.cli export-simulation-corpus --format json --limit 100 > simulations.json
```

Export full knowledge graph with cross-case similarity linkage:

```bash
# Standard graph format (nodes + edges with metadata)
python -m src.core.cli export-graph --format json --similarity-threshold 0.3 --output graph.json

# NetworkX-compatible format (for advanced graph analytics and visualization)
python -m src.core.cli export-graph --format networkx --output graph_networkx.json
```

### Neo4j Graph Persistence (Optional)

For advanced graph analytics and production-scale deployments, sync the knowledge graph to Neo4j:

```bash
# Initialize Neo4j schema (constraints, indexes)
python -m src.core.cli graph-persist --uri bolt://localhost:7687 --username neo4j --password password

# Sync all cases and relationships to Neo4j
python -m src.core.cli graph-sync --uri bolt://localhost:7687 --username neo4j --password password

# Query similar cases by pattern ID
python -m src.core.cli graph-search --query-type similar --pattern-id CVE-2025-0001 --limit 10

# Find all cases mapping to a specific CWE
python -m src.core.cli graph-search --query-type cwe --cwe-id 89 --limit 20

# Cluster cases by focus area
python -m src.core.cli graph-search --query-type focus --focus sql_injection --limit 50

# Show graph statistics
python -m src.core.cli graph-stats --format text
```

**Setup Neo4j locally** (Docker):

```bash
docker run --name logicllama-neo4j \
  -p 7474:7474 -p 7687:7687 \
  -e NEO4J_AUTH=neo4j/password \
  -d neo4j:latest
```

**Environment Variables:**

```bash
NEO4J_URI=bolt://localhost:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=password
NEO4J_DATABASE=neo4j
NEO4J_VERIFY_SSL=true
```

Current runtime boundary:

- Implemented today: SQLite persistence, CLI refresh workflows, Streamlit UI, public-source ingestion, local reference archives, graph traversal, training corpus export, simulation corpus export, cross-case graph linkage, and Neo4j graph persistence layer.
- Planned layers: ChromaDB-backed semantic retrieval, FastAPI service layer, Next.js production UI, and autonomous execution engine.

Run the Streamlit UI:

```bash
streamlit run src/ui/app.py
```

Optional archival utilities for historical datasets:

```bash
python src/ingestion/archive_cwe_snapshots.py
python src/ingestion/archive_kev_snapshots.py
python src/ingestion/curate_owasp_editions.py
```

---

# Core Architecture

```mermaid
flowchart TB
    subgraph UserLayer["User & Research Layer"]
        UI[Web Interface]
        CLI[CLI Interface]
        API[REST API]
    end

    subgraph Intelligence["Reasoning & Intelligence Layer"]
        Planner[Adaptive Planning Engine]
        Decision[Decision Engine]
        Signals[Signal Correlation Engine]
        State[State Machine Engine]
        Evidence[Evidence Graph Engine]
        Hypothesis[Hypothesis Lifecycle Manager]
    end

    subgraph Offensive["Security Analysis Layer"]
        HTTP[HTTP Workflow Analyzer]
        Logic[Business Logic Mapper]
        Race[Concurrency Analyzer]
        Access[Access Control Analyzer]
        Workflow[Workflow State Validator]
    end

    subgraph Knowledge["Knowledge & Learning Layer"]
        RAG[RAG Retrieval Engine]
        Ontology[Logic Ontology Engine]
        Embeddings[Embedding Service]
        Cases[Case Intelligence Store]
    end

    subgraph AI["Local AI Layer"]
        LLM[Local LLM]
        Classifier[Vulnerability Classifier]
        Extractor[Signal Extraction Models]
    end

    subgraph Data["Persistence Layer"]
        Vector[(ChromaDB)]
        Graph[(Neo4j)]
        SQLite[(SQLite)]
        Memory[(Long-Term Memory)]
    end

    UI --> Planner
    CLI --> Planner
    API --> Planner

    Planner --> Decision
    Decision --> Signals
    Signals --> State
    State --> Evidence
   Evidence --> Hypothesis

    Decision --> HTTP
    Decision --> Logic
    Decision --> Race
    Decision --> Access
    Decision --> Workflow

    HTTP --> RAG
    Logic --> Ontology

    RAG --> LLM
    Ontology --> Graph

    Embeddings --> Vector
    Cases --> Vector

    Evidence --> Graph
    Hypothesis --> Memory
```

---

# Intelligence Framework

## Adaptive Planning Engine

Responsible for planned autonomous traversal and execution orchestration.

Capabilities:

- Dynamic attack path generation
- Multi-branch exploration
- Context-aware execution
- Runtime graph traversal
- Failure recovery
- Priority scheduling

---

## Decision Engine

The Decision Engine ranks:

- Attack paths
- Tools
- Hypotheses
- Exploitation branches

Using:

- Weighted rule systems
- Confidence scoring
- Historical success/failure memory
- Adaptive scoring models
- Context-aware prioritization

### Decision Formula

```text
final_score =
base_score
+ matched_rule_weights
+ memory_bias
+ success_learning_boost
- historical_failure_penalty
```

---

## Signal Correlation Engine

Business logic flaws rarely reveal themselves through a single request.

LogicLlama correlates weak signals into high-confidence reasoning.

Examples:

- Response length anomalies
- Timing inconsistencies
- Duplicate transaction states
- Unauthorized transitions
- Workflow desynchronization
- Parallel execution anomalies

---

## State Machine Engine

Applications are reconstructed into explicit workflow states.

LogicLlama identifies:

- Illegal state transitions
- Workflow bypasses
- Missing validations
- Broken sequencing
- Trust violations

Example:

```text
Expected:
Cart → Checkout → Payment → Confirmation

Observed:
Cart → Confirmation
```

---

## Evidence Graph Engine

LogicLlama stores not only findings, but reasoning chains.

Every:

- Signal
- Decision
- Transition
- Hypothesis
- Validation step

becomes part of a causal evidence graph.

This enables:

- Explainable AI reasoning
- Replayable sessions
- Attack path visualization
- Security decision auditing
- Reinforcement learning foundations

---

# Offensive Analysis Modules

## HTTP Workflow Analyzer

Parses:

- Raw HTTP requests
- Burp Suite exports
- Proxy histories
- Session transitions
- Multi-step workflows

Extracts:

- Parameters
- Tokens
- Roles
- Temporal relations
- Workflow dependencies

---

## Business Logic Mapper

Transforms workflows into semantic logic graphs.

Detects:

- Workflow abuse
- Validation gaps
- Economic manipulation
- State inconsistencies
- Trust-boundary violations

---

## Concurrency Analyzer

Focused on temporal vulnerabilities:

- Race conditions
- Double-spend scenarios
- Reward duplication
- Eventual consistency flaws
- Multi-request exploitation

Supports:

- Parallel request simulation
- Race window analysis
- Temporal ordering validation

---

## Access Control Analyzer

Maps:

- Roles
- Resources
- Ownership boundaries
- Session relationships
- Privilege inheritance

Targets:

- IDOR
- Cross-role escalation
- Workflow authorization bypass
- Broken access control

---

# Knowledge & Ontology Layer

## RAG Retrieval Engine

Provides contextual intelligence from:

- PortSwigger Labs
- OWASP BLA
- Public writeups
- CVEs
- Internal research
- User-imported cases

Features:

- Semantic retrieval
- CWE-linked search
- Workflow-aware ranking
- Similarity clustering

---

## Business Logic Ontology

LogicLlama models vulnerabilities as traversable graph structures.

Example:

```text
Race Condition
    ↳ Economic Abuse
        ↳ Coupon Duplication
            ↳ Balance Inflation
```

This enables:

- Cross-pattern reasoning
- Semantic exploit discovery
- Structural vulnerability mapping
- Knowledge graph traversal

---

# Local AI Stack

LogicLlama is fully offline.

No sensitive workflows leave the machine.

## AI Components

- Llama 3.x via Ollama
- Local embeddings
- Local vector search
- Local reasoning pipelines
- Structured rule engines

The LLM assists reasoning.  
It does not blindly control execution.

---

# Temporal & Economic Intelligence

## Temporal Reasoning

Models:

- Request ordering
- Race windows
- Delayed consistency
- Async state propagation
- Synchronization flaws

---

## Economic Logic Layer

Tracks:

- Reward abuse
- Refund amplification
- Credit inflation
- Incentive manipulation
- Multi-account farming
- Transaction desynchronization

---

# Technology Stack

## Frontend

### Current
- Streamlit (Research / Internal UI)

### Future
- Next.js
- React
- Tailwind
- React Flow
- Cytoscape.js

---

## Backend

- FastAPI
- Async Python
- Event-driven architecture

---

## AI & Embeddings

- Ollama
- Llama 3.x
- Instructor Embeddings
- LlamaIndex

---

## Databases

### Neo4j
Graph-native ontology and evidence engine.

### ChromaDB
Semantic retrieval and vector search.

### SQLite
Operational telemetry and local persistence.

---

# Project Structure

```text
LogicLlama/
├── core_reasoning/       # Decision engine and hypothesis systems
├── workflow_analysis/    # HTTP parsing and workflow reconstruction
├── ontology_graph/       # Neo4j schemas and graph traversal
├── ai_stack/             # LLM orchestration and extraction models
├── persistence/          # Database adapters
├── safety_governance/    # Scope validation and execution controls
├── api_gateway/          # REST APIs and CLI routing
├── ui_layer/             # Web interfaces and visualizations
├── schemas/              # Typed reasoning schemas
├── simulations/          # Replay and attack simulations
├── datasets/             # Writeups and training corpora
└── docs/                 # Technical documentation
```

---

# Example Reasoning Flow

```mermaid
flowchart LR
    A[Import Proxy History] --> B[Workflow Reconstruction]
    B --> C[State Graph Generation]
    C --> D[Hypothesis Creation]
    D --> E[Signal Correlation]
    E --> F{Confidence Threshold}

    F -->|Low| G[Alternative Branch]
    F -->|Medium| H[Validation Phase]
    F -->|High| I[Exploit Confirmation]

    I --> J[Evidence Graph Update]
    J --> K[Explainable Report]
```

---

# Safety & Governance

LogicLlama is designed to support bounded autonomous execution.

Controls include:

- Scope validation
- Rate limiting
- Destructive action prevention
- Branch depth limits
- Resource governance
- Human confirmation gates
- Session isolation
- Replay sandboxing

The platform prioritizes:

- Research safety
- Explainability
- Controlled experimentation
- Auditable execution

---

# Roadmap

## Completed

- [x] Local RAG Foundation
- [x] Interactive Mentorship Interface
- [x] Signal Extraction Engine
- [x] Adaptive Decision Layer
- [x] Event-Driven Architecture Migration
- [x] Confidence-Based Traversal Logic

---

## In Progress

- [ ] Neo4j Ontology Integration
- [ ] Automated Workflow Reconstruction
- [ ] Temporal Reasoning Engine
- [ ] Economic Exploitation Modeling
- [ ] Replayable Session Simulator
- [ ] Multi-Branch Autonomous Traversal

---

## Future Research

- [ ] Multi-Agent Security Reasoning
- [ ] Reinforcement Learning from Successful Exploits
- [ ] Autonomous Attack Surface Mapping
- [ ] Cross-Application Behavioral Clustering
- [ ] Interactive Graph Intelligence UI

---

# Research Direction

LogicLlama explores a new category of offensive security:

## Cognitive Offensive Security

Where systems reason about:

- Intent
- Workflow
- Time
- Trust
- Economics
- Human assumptions

instead of simply replaying payloads.

---

# License

MIT License.

---

# Final Statement

The future of application security is not static automation.

It is:

- Workflow intelligence
- State reasoning
- Temporal analysis
- Economic modeling
- Causal inference
- Explainable offensive AI

LogicLlama is building toward that future.
