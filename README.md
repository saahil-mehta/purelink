# Purelink - Data Engineering Co-Pilot

**Agentic system that builds, executes, and validates production-ready data pipelines**

## Overview

Purelink is a **Data Engineering Co-Pilot** that autonomously creates extract-load (EL) pipelines through guided interaction. The agent discovers data sources, designs robust pipelines, and executes them in isolated containers with full validation and monitoring.

**Core Philosophy:** Less code, extremely high quality. Every pipeline must execute successfully before completion.

---

## Quick Start

### Setup
```bash
# Install uv package manager
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install dependencies  
uv pip install ulid-py slugify google-generativeai duckdb python-dateutil requests

# Set API key
export GEMINI_API_KEY="your-gemini-api-key"
```

### Run EL Agent
```bash
# Interactive pipeline creation
python -m purelink.el_agent

# Or with source hint
python -m purelink.el_agent --source "stripe"
```

---

## EL Agent User Flow

### 1. Source Discovery with Auto-Complete

```
EL Agent: I want to extract data from _____

User types: "S"
Auto-complete suggestions:
• Salesforce (CRM platform)
• Stripe (Payment processing)  
• Shopify (E-commerce platform)

User selects: "Stripe"

EL Agent: Found Stripe API. Discovered endpoints:
• customers (Customer records and metadata)
• charges (Payment transactions) 
• subscriptions (Recurring billing data)
• invoices (Billing documents)

Which data would you like to extract?
```

### 2. Requirements Gathering

```
EL Agent: Configuration needed:

1. Complexity Level:
   □ POC (Basic working pipeline)
   □ Production (Robust + monitoring + retry logic)

2. Data & Frequency:
   • Update frequency: One-time / Daily / Hourly
   • Historical data: How far back?

3. Storage: Local DuckDB (default) or cloud warehouse

4. Authentication:
   □ I have API keys ready
   □ I need help getting API keys
```

**API Key Guidance:**
```
EL Agent: I'll guide you through Stripe API setup:

Official Stripe API Key Setup:
1. Dashboard: https://dashboard.stripe.com
2. Navigate: "Developers" → "API keys"  
3. Copy: "Secret key" (sk_test_* for testing)

Once ready, paste here (encrypted locally): [secure input]
API key validated and encrypted
```

### 3. Schema Discovery & Column Selection

```
EL Agent: Probing Stripe API structure...

Analysing 5 sample records from customers endpoint:

Full Schema Detected:
{
  "id": "cus_ABC123...",           // string, required
  "email": "user@example.com",    // string, optional  
  "created": 1638360000,          // timestamp, required
  "address": {...},               // object, nested
  "metadata": {...},              // object, key-values
  "subscriptions": {...}          // complex nested array
}

Column Selection:
[x] Core Fields: id, email, created, name
[x] Contact: phone, address (nested)  
[x] Business: metadata (key-value pairs)
[ ] Complex: subscriptions (may slow extraction)

Continue with selected schema? [Enter for all]
```

### 4. Pipeline Design

```
EL Agent: Creating pipeline architecture:

Pipeline Strategy:
• Extraction: Incremental (using 'created' timestamp)
• Rate Limiting: 100 req/sec (Stripe API limit)
• Pagination: Auto-handle 100 records/page
• Error Recovery: Exponential backoff (3 attempts)
• Data Validation: Email format, required fields
• Storage: Local DuckDB with proper indexing
• Monitoring: Real-time progress + throughput

Production Enhancements (if selected):
• Structured logging with correlation IDs
• Dead letter queue for failed records
• Connection pooling and batch processing

Continue with generation? (y/n)
```

### 5. Code Generation & Validation

```
EL Agent: Generating secure pipeline code...

Authentication Module:
[x] Environment variable integration
[x] Local credential encryption (AES-256)
[x] API key validation and health check

Pipeline Code:  
[x] Extraction with cursor-based pagination
[x] Data validation and sanitisation
[x] Error handling and structured logging
[x] DuckDB schema creation and indexing

Pre-flight Validation:
[x] Static code analysis
[x] Dependency compatibility check
[x] SQL schema validation
[x] Credential access test

Ready for safe execution testing...
```

### 6. Container-Isolated Testing

```
EL Agent: Testing in isolated Docker container...

Container Setup:
• Python 3.11 environment created
• Dependencies: requests, duckdb, pandas
• Secure credential mount
• Monitoring hooks active

Connection Testing:
• API credentials... PASS
• Stripe connectivity... PASS  
• Endpoint permissions... PASS
• Rate limit headers... PASS

Schema Validation:
• Sample records (5)... PASS
• Schema compliance... PASS
• Data type conversion... PASS

Storage Testing:
• DuckDB creation... PASS
• Schema setup... PASS
• Sample writes... PASS

Issues: 0 errors, 1 warning (optional 'phone' field missing)

Ready for full extraction? (y/n)
```

### 7. Live Execution with Monitoring

```
Starting Stripe customers extraction...

Real-Time Progress:
┌─────────────────────────────────────────┐
│ Stripe Customers Pipeline               │
├─────────────────────────────────────────┤  
│ Status: RUNNING                         │
│ Progress: ████████░░░ 1,247/3,421 (36%) │
│ Rate: 95 req/sec (within limit)        │
│ ETA: 2 minutes 15 seconds              │
│ Errors: 0 | Warnings: 3                │
│ Storage: 245 KB → data/stripe.duckdb   │
└─────────────────────────────────────────┘

Press 'q' to stop | 'p' to pause | 'd' for debug
```

**Completion Summary:**
```
Pipeline Complete!

Results:
• Extracted: 3,421 customers
• Success Rate: 99.9% (3 warnings)  
• Duration: 4 minutes 23 seconds
• Storage: 687 KB in DuckDB
• Data Quality: All validations passed

Warnings: 3 empty metadata fields (acceptable)
```

### 8. Recipe Generation & Persistence

```
EL Agent: Creating reusable pipeline recipe...

Recipe: stripe_customers_v1
├── Config: recipes/stripe_customers_v1.yaml
├── Code: pipelines/stripe_customers.py
├── Schema: schemas/stripe_customers.sql  
├── Sample: samples/stripe_preview.json
└── Logs: logs/execution_20240828.log

Version Control:
[x] Recipe committed locally
[x] Execution history tracked
[x] Schema changes versioned

Next Steps:
1. Schedule regular runs (daily/hourly)
2. Add transformation logic (→ TL Agent)
3. Share recipe with team
4. Deploy to production environment

What would you like to do next?
```

---

## Architecture

```
src/
├── el_agent/           # Extract-Load agent core
│   ├── discovery/      # Source + schema detection
│   ├── pipeline/       # Code generation + validation  
│   ├── execution/      # Docker runner + monitoring
│   └── recipes/        # Pipeline persistence
├── utils/              # Shared utilities (LLM, encryption)
└── storage/           # DuckDB interface + cloud adapters
```

**Key Components:**
- **Discovery Engine**: Auto-complete sources, enumerate APIs, detect schemas
- **Pipeline Generator**: Battle-tested code with error handling and monitoring
- **Execution Engine**: Docker isolation with real-time progress tracking
- **Recipe System**: Version-controlled, shareable pipeline configurations
- **Storage Layer**: Local DuckDB with cloud migration paths

---

## Design Principles

**Quality Over Quantity:**
- Every pipeline must execute successfully before completion
- Extensive validation at each step prevents brittle code generation
- Container isolation eliminates environment contamination

**Security First:**
- API keys encrypted locally with AES-256
- Non-destructive operations with confirmation prompts
- Minimal permission scopes and read-only access validation

**Production Ready:**
- Built-in observability with structured logging
- Automatic error recovery with exponential backoff
- Rate limiting and connection pooling for reliability

**User Experience:**
- Claude Code-style interruption and navigation
- Auto-complete and guided setup flows
- Real-time progress monitoring with debugging capabilities

---

## Storage

**Default Local Setup:**
```bash
data/
└── purelink.duckdb     # Unified pipeline data storage
```

**Cloud Migration:**
```python
# Development
from purelink.storage import DuckDBStore
db = DuckDBStore("data/purelink.duckdb")

# Production  
from purelink.storage import BigQueryStore
db = BigQueryStore("project.dataset")
# Same interface, different backend
```

**Recipe Storage:**
```
recipes/
├── stripe_customers_v1.yaml    # Pipeline configuration
├── salesforce_leads_v2.yaml    # Version-controlled recipes
└── shared/                     # Community recipes
```

---

## Commands

```bash
# Interactive EL Agent
python -m purelink.el_agent

# With source hint
python -m purelink.el_agent --source "stripe"

# Recipe management
python -m purelink.recipes list
python -m purelink.recipes run stripe_customers_v1
python -m purelink.recipes share stripe_customers_v1

# Database inspection
python -m purelink.inspect
python -m purelink.inspect --tables
python -m purelink.inspect --query "SELECT * FROM executions"
```

---

## Implementation Status

**Phase 1 - EL Agent Core:**
[ ] Source discovery with auto-complete  
[ ] Requirements gathering and API key guidance
[ ] Schema detection with sample probing
[ ] Pipeline code generation and validation
[ ] Container-isolated execution testing
[ ] Real-time monitoring and progress tracking  
[ ] Recipe creation and version control

**Future Phases:**
[ ] TL Agent (Transform-Load with business logic)
[ ] Recipe sharing and community library
[ ] Cloud deployment automation
[ ] Advanced monitoring dashboards
[ ] Cross-pipeline orchestration

---

**Built with quality-first principles. Battle-tested code only.**