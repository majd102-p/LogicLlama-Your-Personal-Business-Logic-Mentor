# Development Setup Guide

This guide provides detailed instructions for setting up LogicLlama for development.

## Prerequisites

- **Python**: 3.8+ (3.10+ recommended)
- **Git**: For version control
- **Docker** (optional): For Neo4j and containerization
- **pip**: Python package manager

### System Requirements

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| Python | 3.8 | 3.10+ |
| RAM | 4 GB | 8+ GB |
| Disk | 500 MB | 2 GB |

---

## Installation Steps

### 1. Clone Repository

```bash
git clone https://github.com/yourusername/logicllama.git
cd logicllama
```

### 2. Create Virtual Environment

```bash
# Using venv
python -m venv venv

# Activate (Linux/macOS)
source venv/bin/activate

# Activate (Windows PowerShell)
venv\Scripts\Activate.ps1

# Activate (Windows Command Prompt)
venv\Scripts\activate.bat
```

### 3. Install Dependencies

```bash
# Upgrade pip
pip install --upgrade pip setuptools wheel

# Install project dependencies
pip install -r requirements.txt

# Install package in editable mode
pip install -e .
```

### 4. Verify Installation

```bash
# Check CLI works
python -m src.core.cli --help

# Check imports
python -c "from src.core.models import LogicCase; print('✓ OK')"

# Run tests
pytest --version
```

---

## Development Tools

### Install Development Dependencies

```bash
# Code quality tools
pip install black==23.0.0      # Formatter
pip install flake8==5.0.4      # Linter
pip install mypy==1.0.0        # Type checker

# Testing
pip install pytest==7.2.0
pip install pytest-cov==4.0.0
pip install pytest-xdist==3.0.0

# Utilities
pip install ipython pre-commit
```

### Optional: Neo4j Setup

```bash
# Using Docker
docker run -d \
  --name neo4j \
  -p 7474:7474 -p 7687:7687 \
  -e NEO4J_AUTH=neo4j/password \
  neo4j:5.15

# Test connection
python -c "from neo4j import GraphDatabase; d = GraphDatabase.driver('bolt://localhost:7687', auth=('neo4j', 'password')); print('✓ Connected')"
```

---

## Common Development Tasks

### Running Tests

```bash
# All tests
pytest -v

# Specific file
pytest tests/test_cli.py -v

# With coverage
pytest --cov=src --cov-report=html

# Matching pattern
pytest -k "graph" -v

# Parallel execution
pytest -n 4
```

### Code Formatting

```bash
# Format code
black src/ tests/

# Check formatting
black --check src/ tests/

# Format specific file
black src/core/models.py
```

### Linting

```bash
# Check code
flake8 src/ tests/ --max-line-length=100

# Check specific file
flake8 src/core/models.py

# Generate report
flake8 src/ --format=json > flake8_report.json
```

### Type Checking

```bash
# Run mypy
mypy src/ --ignore-missing-imports

# Check specific file
mypy src/core/models.py
```

### Database Operations

```bash
# Initialize database
python -m src.core.cli ingest-fixtures

# Query database
python -m src.core.cli list --source nvd --limit 5

# Check stats
python -m src.core.cli report --analysis coverage

# Audit schema
python -m src.core.cli audit
```

### Neo4j Operations

```bash
# Persist graph
python -m src.core.cli graph-persist

# Run Cypher query
python -m src.core.cli graph-query "MATCH (n:Case) RETURN count(n)"

# Generate stats
python -m src.core.cli graph-stats

# Access Neo4j Browser at http://localhost:7474
```

---

## Git Workflow

### Feature Development

```bash
# Create feature branch
git checkout -b feature/my-feature

# Make changes and commit
git add .
git commit -m "feat(scope): description"

# Push to origin
git push origin feature/my-feature

# Create Pull Request on GitHub
```

### Useful Git Commands

```bash
# See changes
git diff

# View log
git log --oneline -10

# Undo last commit (keep changes)
git reset --soft HEAD~1

# Stash changes
git stash
git stash pop

# Delete branch
git branch -d feature/my-feature
```

---

## Debugging

### Print Debugging

```python
import logging

logger = logging.getLogger(__name__)
logger.debug(f"Searching for: {query}")
```

### Python Debugger

```python
import pdb

def my_function():
    x = 10
    pdb.set_trace()  # Pauses here
    y = x * 2
    return y
```

### Using IPython

```bash
pip install ipython

ipython

# In IPython:
from src.core.storage import StorageManager
storage = StorageManager()
%timeit storage.get_all_cases()
```

---

## Performance Profiling

### CPU Profiling

```python
import cProfile
import pstats

profiler = cProfile.Profile()
profiler.enable()
my_function()
profiler.disable()

stats = pstats.Stats(profiler)
stats.sort_stats('cumulative')
stats.print_stats(10)
```

### Memory Profiling

```bash
pip install memory-profiler

# Create script and run
python -m memory_profiler profile_memory.py
```

---

## Code Quality Workflow

### Quick Quality Check

```bash
#!/bin/bash
echo "🔍 Running quality checks..."

echo "1️⃣ Formatting..."
black src/ tests/ || exit 1

echo "2️⃣ Linting..."
flake8 src/ tests/ --max-line-length=100 || exit 1

echo "3️⃣ Type checking..."
mypy src/ --ignore-missing-imports || exit 1

echo "4️⃣ Running tests..."
pytest -v --cov=src || exit 1

echo "✅ All checks passed!"
```

Save as `check-quality.sh` and run:
```bash
chmod +x check-quality.sh
./check-quality.sh
```

---

## Project Structure

```
logicllama/
├── src/
│   ├── core/              # Core modules (14 files)
│   ├── ingestion/         # Data pipeline (7 files)
│   ├── rag/               # Search functionality
│   ├── ui/                # Streamlit interface
│   └── analysis/          # Analysis tools
├── tests/                 # Test suite (7 files)
├── data/                  # Data files
├── docs/                  # Documentation
├── database/              # SQLite database
├── requirements.txt       # Dependencies
├── README.md
├── CONTRIBUTING.md
├── ARCHITECTURE.md
├── DEVELOPMENT.md         # This file
└── .github/               # GitHub workflows
```

---

## Troubleshooting

### ImportError for src module

```bash
# Add to PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

# Or install in development mode
pip install -e .
```

### Database file not found

```bash
# Initialize database
python -m src.core.cli ingest-fixtures
```

### Neo4j connection failed

```bash
# Check if running
docker ps | grep neo4j

# Start Neo4j
docker run -d neo4j:5.15
```

### Port already in use

```bash
# Find process using port (macOS/Linux)
lsof -i :7687

# Kill process
kill -9 <PID>
```

---

## Next Steps

1. Read [ARCHITECTURE.md](./ARCHITECTURE_PROFESSIONAL.md)
2. Read [CONTRIBUTING.md](./CONTRIBUTING_PROFESSIONAL.md)
3. Explore `src/core/models.py`
4. Run tests: `pytest`
5. Start developing!

---

**Document Version**: 1.0  
**Last Updated**: May 9, 2026
