# GitHub Deployment & Secrets Configuration

This guide covers configuring GitHub Secrets and deploying LogicLlama.

## Setting Up GitHub Secrets

To enable RAG features with LLM integration and CI workflows:

### 1. OpenAI API Key (Optional for RAG)

If you want to use the OpenAI LLM client for RAG features:

1. Navigate to your repository on GitHub
2. Go to **Settings** → **Secrets and variables** → **Actions**
3. Click **New repository secret**
4. Name: `OPENAI_API_KEY`
5. Value: Your OpenAI API key (get one from [platform.openai.com](https://platform.openai.com/account/api-keys))
6. Click **Add secret**

The CI workflow (`.github/workflows/ci.yml`) and RAG client (`src/rag/openai_client.py`) will automatically use this secret when available.

### 2. (Optional) PyPI Publishing

To automatically publish releases to PyPI:

1. Create a PyPI token at [pypi.org/account/](https://pypi.org/account/)
2. Add as secret `PYPI_API_TOKEN` (instructions similar to above)
3. Update `.github/workflows/ci.yml` to include a publish step (currently not configured)

## CI/CD Workflow

The repository includes a GitHub Actions workflow (`.github/workflows/ci.yml`) that:

- Runs on every push and pull request to `main`
- Tests across Python 3.8, 3.9, 3.10, 3.11, 3.12
- Installs the editable package and runs pytest
- Uses `OPENAI_API_KEY` if available (gracefully skips if missing)

View workflow runs under **Actions** tab in your repository.

## Releasing a New Version

1. Update version in `pyproject.toml` (currently `version = "0.1.0"`)
2. Commit changes
3. Tag release: `git tag -a v<VERSION> -m "v<VERSION> release notes"`
4. Push tag: `git push origin v<VERSION>`
5. GitHub Actions will run tests automatically
6. (Optional) Create GitHub Release from tag with notes from `docs/releases/v<VERSION>.md`

## Local Development

To set up local environment with optional LLM support:

```bash
# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .\.venv\Scripts\Activate.ps1

# Install editable package
pip install -e .

# Set OpenAI API key (optional, for RAG features)
export OPENAI_API_KEY=sk-...
# On Windows: $env:OPENAI_API_KEY="sk-..."

# Run Streamlit UI
streamlit run src/ui/app.py

# Use CLI
logicllama --help
```

## Troubleshooting

- **CI tests fail**: Check GitHub Actions logs under **Actions** tab
- **OpenAI client errors**: Verify `OPENAI_API_KEY` secret is set correctly and API key is active
- **Package installation fails**: Ensure Python ≥3.8 and pip/setuptools are up to date
