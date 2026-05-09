# Contributing to LogicLlama

First off, thank you for considering a contribution to LogicLlama! It's people like you that make LogicLlama such a great tool.

## Code of Conduct

This project and everyone participating in it is governed by our Code of Conduct. By participating, you are expected to uphold this code. Please report unacceptable behavior to project maintainers.

---

## How Can I Contribute?

### Reporting Bugs

Before creating bug reports, please check the [issue list](https://github.com/yourusername/logicllama/issues) as you might find out that you don't need to create one. When you are creating a bug report, please include as many details as possible:

**Use the bug report template:**
- Clear, descriptive title
- Exact steps to reproduce
- Specific examples to demonstrate steps
- Behavior description (what you observed vs. expected)
- Screenshots/logs if applicable
- System info (OS, Python version, Neo4j version if applicable)

**Example:**
```
Title: Search command fails with special characters

Steps to Reproduce:
1. Run: `python -m src.core.cli search --query "SQL' OR '1'='1"`
2. Expected: Returns filtered results
3. Actual: Raises encoding error

Environment:
- OS: Windows 10
- Python: 3.9.5
- Database: SQLite + Neo4j 5.15
```

### Suggesting Enhancements

Enhancement suggestions are tracked as GitHub issues. When creating an enhancement suggestion, please include:

- Clear, descriptive title
- Step-by-step description of suggested enhancement
- Specific examples to demonstrate steps
- Description of current behavior vs. expected behavior
- Why this enhancement would be useful

**Example:**
```
Title: Add JSON output format to CLI commands

Suggestion:
Add --format json flag to all CLI commands for easier integration with other tools.

Use Case:
Would allow piping results directly to jq for filtering and analysis.

Example:
python -m src.core.cli search --query "injection" --format json | jq '.[] | .cwe'
```

---

## Pull Request Process

1. **Fork the repository** and create your branch from `main`
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Install development dependencies**
   ```bash
   pip install -r requirements.txt
   pip install -e .  # Install package in development mode
   ```

3. **Make your changes**
   - Keep commits atomic and focused
   - Follow PEP 8 style guide
   - Write clear, descriptive commit messages
   - Add tests for new functionality

4. **Write or update tests**
   ```bash
   # For new features, add tests in tests/
   # Example: if adding CLI command, add test in tests/test_cli.py
   pytest tests/test_your_feature.py -v
   ```

5. **Format and lint your code**
   ```bash
   # Format with black
   black src/ tests/
   
   # Check linting
   flake8 src/ tests/ --max-line-length=100
   
   # Type checking
   mypy src/ --ignore-missing-imports
   ```

6. **Run full test suite**
   ```bash
   pytest -v --cov=src
   ```

7. **Update documentation**
   - Update README.md if needed
   - Add docstrings to new functions/classes
   - Update ARCHITECTURE.md if architectural changes

8. **Commit and push**
   ```bash
   git commit -m "Clear message describing change"
   git push origin feature/your-feature-name
   ```

9. **Submit a Pull Request**
   - Fill out the PR template completely
   - Link related issues (if any)
   - Provide context and rationale for changes
   - Request review from maintainers

---

## Development Setup

### Environment Setup

```bash
# Clone repository
git clone https://github.com/yourusername/logicllama.git
cd logicllama

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install development tools
pip install black flake8 mypy pytest pytest-cov

# Optional: Setup Neo4j for testing
docker run -d \
  -p 7474:7474 -p 7687:7687 \
  -e NEO4J_AUTH=neo4j/password \
  neo4j:5.15
```

### Running Tests Locally

```bash
# Run all tests
pytest -v

# Run specific test file
pytest tests/test_cli.py -v

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test by name
pytest tests/test_cli.py::test_search_command -v

# Run tests matching pattern
pytest -k "graph" -v
```

### Code Quality Checks

```bash
# Format code
black src/ tests/

# Check formatting
black --check src/ tests/

# Lint code
flake8 src/ tests/ --max-line-length=100

# Type checking
mypy src/ --ignore-missing-imports

# All checks together
black src/ && flake8 src/ && mypy src/
```

---

## Contribution Areas

### 🐛 Bug Fixes
- Look for [good-first-issue](https://github.com/yourusername/logicllama/labels/good-first-issue) labels
- Check [help-wanted](https://github.com/yourusername/logicllama/labels/help-wanted) issues
- Check existing tests - they might catch bugs

### ✨ New Features
Popular areas:
- **New Data Source Adapters**: Implement `SourceAdapter` interface
- **CLI Commands**: Add new commands following existing patterns
- **UI Enhancements**: Improve Streamlit dashboard
- **Analysis Tools**: Add new analysis capabilities
- **Graph Queries**: Add sophisticated Neo4j queries

### 📚 Documentation
- Improve README.md and existing docs
- Add usage examples
- Create tutorial guides
- Fix typos and unclear passages
- Add inline code documentation

### 🧪 Tests
- Add edge case tests
- Improve test coverage
- Add integration tests
- Performance benchmarks

### ⚡ Performance
- Profile and optimize slow code paths
- Improve database query performance
- Reduce memory usage
- Optimize graph operations

---

## Adding a New Data Source

Example: Adding a custom vulnerability source

1. **Create adapter in `src/ingestion/adapters.py`**
   ```python
   class MySourceAdapter(SourceAdapter):
       def __init__(self):
           super().__init__(
               name="MySecurity",
               description="My security vulnerability database",
               url="https://example.com/api"
           )
       
       def extract(self) -> List[LogicCase]:
           """Extract cases from source."""
           cases = []
           # Implementation here
           return cases
   ```

2. **Add tests in `tests/test_public_source_adapters.py`**
   ```python
   def test_my_source_adapter_extraction():
       adapter = MySourceAdapter()
       cases = adapter.extract()
       assert len(cases) > 0
       assert all(isinstance(c, LogicCase) for c in cases)
   ```

3. **Register in pipeline in `src/ingestion/pipeline.py`**
   ```python
   ADAPTERS = [
       NVDAdapter(),
       CWEAdapter(),
       KEVAdapter(),
       OWASPAdapter(),
       PortSwiggerAdapter(),
       MySourceAdapter(),  # Add here
   ]
   ```

4. **Update documentation in `docs/DATA_SOURCES.md`**

5. **Run tests and submit PR**

---

## Adding a New CLI Command

Example: Adding a statistics command

1. **Define command in `src/core/cli.py`**
   ```python
   @click.command('statistics')
   @click.option('--source', type=str, help='Filter by source')
   def statistics(source):
       """Generate detailed statistics report."""
       # Implementation
       click.echo(result)
   ```

2. **Add test in `tests/test_cli.py`**
   ```python
   def test_statistics_command():
       runner = CliRunner()
       result = runner.invoke(cli, ['statistics'])
       assert result.exit_code == 0
       assert 'statistics' in result.output.lower()
   ```

3. **Document in docstring**
4. **Update README.md with usage example**
5. **Test locally and submit PR**

---

## Code Style Guidelines

### Python Style (PEP 8)
- Use 4 spaces for indentation
- Max line length: 100 characters
- Use descriptive variable names
- Write docstrings for all functions/classes

### Example:
```python
def search_cases(query: str, limit: int = 10) -> List[LogicCase]:
    """
    Search for security cases matching query.
    
    Args:
        query: Search string
        limit: Maximum results to return
    
    Returns:
        List of matching LogicCase objects
    
    Raises:
        ValueError: If query is empty
    """
    if not query:
        raise ValueError("Query cannot be empty")
    
    # Implementation
    return results
```

### Type Hints
- Always use type hints for function parameters and returns
- Use typing module for complex types

```python
from typing import List, Optional, Dict, Any

def process_data(
    items: List[str],
    config: Optional[Dict[str, Any]] = None
) -> bool:
    """Process items with optional configuration."""
    pass
```

### Imports
```python
# Standard library imports first
import os
import sys
from typing import List, Dict

# Third-party imports
import click
from pydantic import BaseModel

# Local imports
from src.core.models import LogicCase
from src.ingestion.adapters import SourceAdapter
```

---

## Commit Message Guidelines

Write clear, atomic commits:

```
<type>(<scope>): <subject>

<body>

<footer>
```

**Types:**
- `feat`: A new feature
- `fix`: A bug fix
- `docs`: Documentation only
- `style`: Changes that don't affect code meaning
- `refactor`: Code change that improves structure
- `perf`: Performance improvements
- `test`: Adding or updating tests
- `chore`: Build, CI/CD, or dependency changes

**Examples:**
```
feat(search): add fuzzy matching support

Add fuzzy search option to CLI search command using fuzzywuzzy library.
Allows approximate matching for typos in queries.

Fixes #123

feat(graph): implement similarity scoring algorithm

Calculate cross-case similarity using Jaccard distance and CWE relationships.
Exported as edges in Neo4j graph.

- Add similarity computation in graph_builder.py
- Add tests for edge cases
- Update documentation

fix(cli): handle special characters in query strings

SQL injection patterns now handled correctly with proper escaping.

Fixes #456
```

---

## Testing Guidelines

### Test Structure
```python
import pytest
from src.core.models import LogicCase
from src.ingestion.adapters import NVDAdapter

class TestNVDAdapter:
    """Test suite for NVD adapter."""
    
    @pytest.fixture
    def adapter(self):
        """Create adapter instance."""
        return NVDAdapter()
    
    def test_extraction_returns_cases(self, adapter):
        """Test that extraction returns LogicCase instances."""
        cases = adapter.extract()
        assert len(cases) > 0
        assert all(isinstance(c, LogicCase) for c in cases)
    
    def test_cve_format_validation(self, adapter):
        """Test CVE ID format validation."""
        cases = adapter.extract()
        for case in cases[:10]:  # Sample first 10
            assert case.cve_id.startswith("CVE-")
```

### Coverage Requirements
- Minimum 80% coverage for new code
- All public functions should have tests
- Edge cases and error conditions should be tested

---

## Documentation Guidelines

### Docstring Format
Use Google-style docstrings:

```python
def calculate_similarity(case1: LogicCase, case2: LogicCase) -> float:
    """
    Calculate similarity between two security cases.
    
    Similarity is based on CWE mappings and keyword overlap.
    
    Args:
        case1: First security case
        case2: Second security case
    
    Returns:
        Similarity score between 0.0 and 1.0
    
    Raises:
        ValueError: If cases are None or invalid
    
    Example:
        >>> case1 = LogicCase(cve_id="CVE-2021-1234", ...)
        >>> case2 = LogicCase(cve_id="CVE-2021-5678", ...)
        >>> score = calculate_similarity(case1, case2)
        >>> print(f"Similarity: {score:.2%}")
        Similarity: 45.32%
    """
```

---

## Review Process

### What to Expect
1. Maintainers review PR within 2-5 business days
2. We may request changes using GitHub suggestions
3. You can dismiss suggestions with reasoning if you disagree
4. Once approved, PR is merged

### Common Review Comments
- "Add tests for this functionality"
- "Can you simplify this logic?"
- "Update the docstring"
- "Add type hints"
- "Performance consideration here"

### Addressing Review Comments
```bash
# Make requested changes
git add <files>
git commit -m "Address review comments"
git push origin feature/your-feature-name

# Do NOT force push to PR - maintainers need to see the updates
# Do NOT create a new PR - update the existing one
```

---

## Resources

- [Git Documentation](https://git-scm.com/doc)
- [Python PEP 8](https://pep8.org/)
- [Pytest Documentation](https://docs.pytest.org/)
- [GitHub Flavored Markdown](https://github.github.com/gfm/)

---

Thank you for contributing! 🎉

**Happy coding!**
