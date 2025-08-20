# UV Package Manager Quickstart

## Setup Environment

```bash
# Install dependencies
uv pip install -e .

# Alternative: Install specific packages
uv pip install google-genai python-ulid python-slugify
```

## Common Commands

```bash
# Install new dependency
uv pip install package-name

# Install dev dependencies
uv pip install --dev pytest black ruff

# Show installed packages
uv pip list

# Generate requirements
uv pip freeze > requirements.txt

# Sync from lock file
uv pip sync requirements.txt
```

## Environment Variables

```bash
# Set Gemini API key
export GOOGLE_API_KEY="your-api-key-here"

# Alternative
export GEMINI_API_KEY="your-api-key-here"
```

## Running Purelink

```bash
# Intent capture workflow
python main.py capture

# Method discovery workflow  
python main.py discovery

# Show help
python main.py --help
```