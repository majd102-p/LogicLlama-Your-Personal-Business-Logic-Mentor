# LogicLlama: Your Personal Business Logic Mentor

![LogicLlama](https://via.placeholder.com/800x200/0A2540/00FFAA?text=LogicLlama)

**A fully local, privacy-first AI mentor specialized in Business Logic Vulnerabilities.**

---

## Overview

**LogicLlama** is an intelligent, offline AI-powered mentor designed specifically to help penetration testers, bug bounty hunters, and security researchers master **Business Logic Vulnerabilities** (Logic Flaws).

It acts as a personal tutor that provides interactive learning, contextual analysis of HTTP requests, visual explanations, and structured progress tracking — all while running **100% locally** to ensure complete privacy and data security.

---

## The Problem

Business Logic Vulnerabilities remain one of the hardest categories to detect and learn:

- Automated security scanners cannot understand business context and rules.
- Cloud-based LLMs pose significant privacy risks when analyzing sensitive HTTP requests or internal application logic.
- Quality educational materials are scattered across different platforms and difficult to study systematically.

---

## Our Solution

LogicLlama solves these challenges by combining a powerful local LLM with a carefully curated knowledge base using Retrieval-Augmented Generation (RAG). The entire system runs offline on your machine.

---

## Architecture

### High-Level Component Diagram

```mermaid
flowchart TB
    subgraph User["User Layer"]
        UI[Streamlit Dashboard]
    end

    subgraph Core["Core Application"]
        Analyzer[HTTP Request Analyzer]
        Challenge[Challenge Mode Engine]
        RAG[RAG Engine]
        Visual[Visualization Engine]
        Progress[Progress Tracker]
    end

    subgraph AI["AI & Knowledge Layer"]
        LLM[Local LLM\nLlama 3.1/3.2 via Ollama]
        VectorDB[Vector Database\nChromaDB]
    end

    subgraph Data["Data Layer"]
        SQLite[(SQLite\nProgress DB)]
        RawData[Raw Writeups\nPortSwigger + OWASP]
    end

    UI --> Analyzer
    UI --> Challenge
    UI --> Progress
    UI --> Visual

    Analyzer --> RAG
    Challenge --> RAG
    RAG --> LLM
    RAG --> VectorDB
    VectorDB --> RawData

    Progress --> SQLite
    Visual --> RAG
```

---

## Key Features

- **Challenge Mode**: Learn through realistic scenarios with interactive evaluation and hints.
- **HTTP Request Analyst**: Paste raw HTTP requests from Burp Suite or any proxy to detect potential logic flaws.
- **Smart Tool Advisor**: Get tailored recommendations for tools and testing methodologies.
- **Visual Logic Flow**: Generate clear Mermaid diagrams comparing normal vs. vulnerable workflows.
- **Progress Tracker**: Track your learning progress with personal notes using SQLite.

---

## Use Cases

### Supported Use Cases
```mermaid
 flowchart TD
    Actor[Security Researcher\n/Pentester\n/Bug Bounty Hunter] 
    
    subgraph System["LogicLlama System"]
        UC1[Start Interactive Challenge]
        UC2[Analyze HTTP Request for Logic Flaws]
        UC3[View Learning Progress]
        UC4[Browse Knowledge Base\nby OWASP BLA Category]
        UC5[Generate Visual Logic Flow - Mermaid]
        UC6[Receive Smart Tool Recommendations]
        UC7[Add Personal Notes to Case]
        UC8[Import Personal Writeups]
    end

    Actor --> UC1
    Actor --> UC2
    Actor --> UC3
    Actor --> UC4
    Actor --> UC5
    Actor --> UC6
    Actor --> UC7
    Actor --> UC8

    UC2 -.-> UC5
    UC1 -.-> UC5
    UC1 -.-> UC6
```

---

## Core System Design

### High-Level Class Diagram
```mermaid
classDiagram
    class LogicLlamaApp {
        +RAGEngine ragEngine
        +ChallengeManager challengeManager
        +HTTPRequestAnalyzer httpAnalyzer
        +ProgressTracker progressTracker
        +Visualizer visualizer
        +initialize()
        +run()
    }

    class RAGEngine {
        +VectorDatabase vectorDB
        +LocalLLM llm
        +query(query: str) RAGResponse
        +retrieveSimilarCases(context: str) List~BusinessLogicCase~
    }

    class HTTPRequestAnalyzer {
        +analyzeRequest(rawRequest: str) AnalysisResult
        +detectLogicFlaws(request: HttpRequest) List~Vulnerability~
    }

    class ChallengeManager {
        +loadChallenge(id: str) Challenge
        +validateAnswer(userAnswer: str, challengeId: str) ValidationResult
        +generateHint() str
    }

    class ProgressTracker {
        +saveProgress(userId: str, caseId: str, score: int)
        +getUserProgress() ProgressStats
        +addNote(caseId: str, note: str)
    }

    class Visualizer {
        +generateMermaidFlow(logicSteps: List) str
        +renderDiagram(diagramType: str)
    }

    class BusinessLogicCase {
        +caseId: str
        +title: str
        +flawType: str
        +owaspCategory: str
        +domain: str
        +description: str
        +attackScenario: str
        +prevention: str
    }

    LogicLlamaApp "1" --> "1" RAGEngine
    LogicLlamaApp "1" --> "1" HTTPRequestAnalyzer
    LogicLlamaApp "1" --> "1" ChallengeManager
    LogicLlamaApp "1" --> "1" ProgressTracker
    LogicLlamaApp "1" --> "1" Visualizer

    RAGEngine "1" --> "*" BusinessLogicCase
    RAGEngine --> LocalLLM
    RAGEngine --> VectorDatabase
```

---

## Technology Stack

- **Large Language Model**: Llama 3.1 / 3.2 via Ollama (fully local)
- **RAG Framework**: LlamaIndex
- **Vector Database**: ChromaDB
- **Frontend**: Streamlit
- **Progress & Notes**: SQLite
- **Visualization**: Mermaid.js
- **All components run offline** after initial setup

---

## Project Structure

```plaintext
LogicLlama/
├── data/
│   ├── raw/                    # Original writeups and labs
│   └── processed/              # Processed and chunked documents
├── src/
│   ├── ingestion/              # Data ingestion and embedding pipeline
│   ├── rag/                    # RAG engine and retrieval logic
│   ├── analysis/               # HTTP Request Analyzer & Challenge logic
│   ├── core/                   # Main application services
│   └── ui/                     # Streamlit user interface
├── database/
│   └── progress.db             # SQLite database for user progress
├── docs/
│   └── diagrams/               # UML and architecture diagrams
├── README.md
├── requirements.txt
├── pyproject.toml
└── .env.example

## Getting Started

Detailed installation and setup instructions will be added once the core functionality is implemented.

### Prerequisites

- Python 3.11 or higher
- Ollama with Llama 3.1 or 3.2 model
- Git



## Roadmap

- Phase 1: Data Ingestion Pipeline & RAG Foundation
- Phase 2: Streamlit UI + Progress Tracker
- Phase 3: Challenge Mode + HTTP Request Analyst
- Phase 4: Visualization Engine & Tool Advisor
- Phase 5: Performance Optimization & Docker Support
- Phase 6: Documentation & Open Source Release

## Contributing
Contributions are welcome! Whether it's improving the knowledge base, enhancing prompts, fixing bugs, or adding new features — feel free to open an issue or submit a pull request.
See CONTRIBUTING.md for more details.

## License

This project is licensed under the MIT License.

Built with focus on privacy, education, and deep technical understanding.