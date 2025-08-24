# Purelink Data Engineering Agent

**Local POC for vertical data ingestion workflows**

## Overview

Purelink implements a sequential agent workflow for data engineering: 
**User Input → Tool Resolution → Method Discovery → Credential Collection → Data Extraction**

The agent uses LLM-powered resolution with intelligent caching and 30-day method expiration for cost efficiency.

## Setup

### Install UV Package Manager
```bash
# Install uv (if not already installed)
curl -LsSf https://astral.sh/uv/install.sh | sh    # Unix/Mac
# Windows: powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

# Install dependencies
uv pip install -e .
```

### Set API Key
```bash
# Unix/Mac
export GEMINI_API_KEY="your-key-here"
# Windows: set GEMINI_API_KEY=your-key-here
```

## Usage

```bash
# Run complete workflow (interactive)
python main.py workflow

# Or run phases individually (interactive)
python main.py capture
python main.py discovery

# Non-interactive modes (automation)
python main.py capture --input "salesforce"
python main.py discovery --candidate-id "salesforce-abc123"
```

## Architecture

```
src/
├── core/           # Workflow orchestration
├── capture/        # Intent capture with LLM + store
├── discovery/      # Method discovery with expiration 
└── utils/          # Shared utilities

data/
├── capture-intent/     # Candidates (permanent)
└── discover-methods/   # Methods (30-day expiry)
```

## Commands

- `capture` - Resolve user input to tool candidates
- `discovery` - Discover ingestion methods for tools
- `workflow` - Run complete capture→discovery sequence with user confirmations

## Features

- **Smart Caching**: Reuses candidate/method data to reduce LLM costs
- **Method Expiration**: 30-day TTL ensures method freshness 
- **Interactive + Automation**: Workflow maintains user confirmations; individual commands support `--input` flags for automation
- **Data Persistence**: JSONL storage for audit trails and analytics
- **Type Safety**: TypedDict schemas throughout

## Documentation

- **[Workflow Guide](workflow-guide.md)** - Complete usage and architecture details

## Implementation Status

✅ Intent capture with candidate store  
✅ Method discovery with expiration  
✅ Sequential workflow orchestration  
🚧 Credential collection (next phase)  
⏳ Connection testing  
⏳ Data extraction