# Purelink Complete Workflow Guide

**Comprehensive guide to the data engineering agent implementation**

## Overview

Purelink implements a sequential data engineering agent workflow:

```
User Input → Tool Resolution → Method Discovery → Credential Collection → Data Extraction
```

## Workflow Visual

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────────┐
│   User Input    │───→│  Intent Capture  │───→│  Method Discovery   │
│  "salesforce"   │    │                  │    │                     │
│                 │    │ • LLM Resolution │    │ • Check Store First │
│                 │    │ • Candidate Store│    │ • LLM if Needed     │
│                 │    │ • Confirmation   │    │ • Method Selection  │
└─────────────────┘    └──────────────────┘    └─────────────────────┘
                                │                         │
                                ▼                         ▼
                       ┌──────────────────┐    ┌─────────────────────┐
                       │   Data Storage   │    │   Next Phase        │
                       │                  │    │                     │
                       │ candidates.jsonl │    │ • Credential Setup  │
                       │ capture-logs/    │    │ • Connection Test   │  
                       │ method-logs/     │    │ • Data Extraction   │
                       └──────────────────┘    └─────────────────────┘
```

## Commands

### Individual Commands

```bash
# Step 1: Capture tool intent
python main.py capture --input "salesforce"
# Returns: candidate_id (e.g., salesforce-dedbeaee732f)

# Step 2: Discover methods using candidate ID
python main.py discovery --candidate-id "salesforce-dedbeaee732f"
```

### Sequential Workflow

```bash
# Complete workflow with user confirmations (recommended)
python main.py workflow
```

## Data Reuse Strategy

### Capture Stage
- **First Query**: Input → LLM → Store candidate (permanent)
- **Subsequent Queries**: Input → Check Store → Return existing or query LLM

### Discovery Stage  
- **First Discovery**: Candidate ID → LLM → Store methods (30-day expiry)
- **Subsequent Discovery**: Candidate ID → Check Store → Validate expiry → Return existing or re-query LLM

### Method Expiration
Method discoveries include **30-day expiration timestamps** to ensure data freshness:
- **Fresh Methods**: Stored methods used directly (< 30 days old)
- **Expired Methods**: Automatic LLM re-query for updated method information
- **Transparency**: Shows expiration info ("expires in 15 days") in output

### Storage Structure
```
data/
├── capture-intent/
│   ├── candidates.jsonl    # Reusable candidates (permanent)
│   ├── index.jsonl         # All capture sessions  
│   └── logs/              # Individual session files
└── discover-methods/
    ├── index.jsonl         # All discovery sessions (with expiry)
    └── logs/              # Individual method files
```

### Expiration Example
```json
{
  "data": {
    "methods": [...],
    "expires_at": "2025-09-19T15:22:07.692702+00:00",
    "discovery_source": "llm-powered"
  }
}
```

## Workflow Command Behaviour

**Sequential orchestration with clean separation of concerns:**

```
WORKFLOW COMMAND: python main.py workflow

CAPTURE PHASE (capture_main()):
├── User Input (interactive prompt)
├── Store Check (avoid LLM re-query)
├── LLM Resolution (if needed)
├── Tool Confirmation (user confirms correct tool)
└── → Candidate ID

DISCOVERY PHASE (discovery_main(candidate_id, non_interactive=False)):
├── Uses Candidate ID (skips capture intent)
├── Method Store Check (avoid LLM re-query)
├── Expiration Validation (30-day TTL)
├── LLM Discovery (if expired or missing)
├── Method Selection (user selects method)
└── → Method Record (with expiry)

NEXT PHASE:
├── Credential Collection
├── Connection Testing  
└── Data Extraction
```

**Key Design Principle:**
- **No duplicate steps**: Capture does intent capture, Discovery does method discovery
- **User confirmations preserved**: Both tool selection and method selection require user input
- **Smart caching**: Each phase checks stores before LLM queries

## Implementation Details

### Core Features
- **Sequential Coupling**: Capture produces candidate_id for discovery
- **Smart Caching**: Candidates stored permanently, methods cached with expiration  
- **Method Expiration**: 30-day TTL with automatic LLM refresh
- **Type Safety**: TypedDict schemas throughout for runtime validation
- **Non-Interactive**: Automation-friendly with auto-confirm/select modes

### Storage Architecture
```
data/
├── capture-intent/
│   ├── candidates.jsonl    # Permanent candidate store
│   ├── index.jsonl         # All capture sessions
│   └── logs/01K*.json      # Individual session records
└── discover-methods/
    ├── index.jsonl         # All discovery sessions (with expiry)
    └── logs/01K*.json      # Individual method records
```

### Method Expiration System
Every method discovery includes expiration metadata:
```json
{
  "data": {
    "methods": [...],
    "expires_at": "2025-09-19T15:32:06+00:00",
    "discovery_source": "llm-powered"
  }
}
```

### Command Examples

```bash
# Set API key (required)
export GEMINI_API_KEY="your-api-key"

# Individual commands (interactive)
python main.py capture
python main.py discovery

# Non-interactive mode
python main.py capture --input "salesforce"
python main.py discovery --candidate-id "salesforce-abc123"

# Complete workflow with user confirmations (recommended)
python main.py workflow
```

## Error Handling

- **Missing API Key**: Commands fail fast with clear error
- **Invalid Candidate ID**: Discovery shows error, stops gracefully  
- **No Methods Found**: Workflow stops, shows diagnostic info
- **Store Corruption**: Falls back to LLM queries
- **Expired Methods**: Automatic LLM re-query with expiration notice
- **Malformed Expiry**: Treats as expired, forces refresh