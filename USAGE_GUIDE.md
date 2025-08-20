# PureLink Data Engineering Agent - Usage Guide

## Overview and Context

PureLink is a local Proof of Concept (POC) for a vertical Data Engineering Agent designed to streamline the process of discovering, connecting to, and extracting data from various SaaS tools and platforms. The agent follows a structured workflow that takes users from initial intent expression through to configured data extraction methods.

### Agent Workflow Philosophy

The system operates on the principle of **progressive refinement** - starting with natural language intent and systematically narrowing down to specific, actionable data extraction configurations. This approach minimises cognitive load on users while maximising precision in the final implementation.

**Core Workflow:**
```
User Intent → Tool Resolution → Method Discovery → Credential Collection → Data Extraction
     ↓              ↓                ↓                    ↓               ↓
   "I need        Salesforce      REST API v1         OAuth 2.0      JSON Records
Salesforce data"    CRM          + Endpoints        + API Keys      + Local Storage
```

The agent is designed for **local execution** with no external infrastructure dependencies beyond the Gemini API for LLM-powered resolution and discovery. All data, configurations, and workflow state are persisted locally using append-only JSONL files for auditability and reproducibility.

---

## Technical Architecture

### Component Structure

```
mvp/
├── capture_intent_poc_v2.py          # Phase 1: Intent capture and tool resolution
├── discover_methods_poc_v1.py        # Phase 2: Hardcoded method discovery (legacy)  
├── discover_methods_poc_v2.py        # Phase 2: Integrated LLM-powered workflow
└── capture-intent/                   # Intent capture storage
    ├── candidates/
    │   └── candidates.jsonl          # Normalised tool candidates store
    ├── logs/                         # Individual intent records (ULID-named)
    └── index.jsonl                   # Append-only intent record index

discover-methods/                     # Method discovery storage
├── logs/                            # Individual method records (ULID-named)  
└── index.jsonl                     # Append-only method record index
```

### Data Flow Architecture

**Storage Pattern:**
- **Dual Persistence**: Individual JSON files (random access) + JSONL index (streaming analytics)
- **ULID Identifiers**: Time-sortable unique IDs for chronological ordering
- **Schema Versioning**: Version fields for evolutionary compatibility
- **Immutable Records**: Append-only pattern for complete audit trail

**Type System:**
- **TypedDict Schemas**: Runtime-type-safe data structures
- **Literal Types**: Constrained enums for record kinds and sources
- **Optional Fields**: NotRequired for flexible schema evolution

### LLM Integration

**Gemini 2.5 Flash Configuration:**
```python
client = genai.Client(api_key=api_key)
model = "gemini-2.5-flash"

# Tool resolution: Structured JSON with schema enforcement
config = types.GenerateContentConfig(
    response_mime_type="application/json",
    response_schema=ToolResolution,
    temperature=0,  # Deterministic
    max_output_tokens=512
)

# Method discovery: Creative generation with higher limits  
config = types.GenerateContentConfig(
    temperature=0.3,  # Slightly creative
    max_output_tokens=4096  # Complex method descriptions
)
```

---

## Usage Instructions

### Prerequisites

**Environment Setup:**
```bash
# Install dependencies
uv pip install google-genai ulid-py python-slugify

# Set API key (required)
export GOOGLE_API_KEY="your-gemini-api-key"
```

**API Key Configuration:**
- Obtain API key from [Google AI Studio](https://aistudio.google.com/)
- Set as environment variable (preferred) or modify script directly
- Supports both `GOOGLE_API_KEY` and `GEMINI_API_KEY`

### Basic Workflow Execution

**Integrated Workflow (Recommended):**
```bash
cd mvp
python discover_methods_poc_v2.py
```

**Phase-by-Phase Execution:**
```bash
# Phase 1: Capture intent only
python capture_intent_poc_v2.py

# Phase 2: Discover methods for existing candidate
python discover_methods_poc_v1.py  # Legacy hardcoded
```

### Input Specifications

**Intent Expression Examples:**
```
✅ Good: "I need Salesforce customer data"
✅ Good: "HubSpot CRM contacts and deals" 
✅ Good: "Slack message history export"
✅ Good: "Monday.com project data"

❌ Avoid: "data"
❌ Avoid: "some CRM thing"
❌ Avoid: "the usual stuff"
```

**Tool Confirmation:**
- System presents resolved tool with metadata
- User confirms with `y`/`yes` or rejects with `n`/`no`
- Rejected tools trigger retry with supplementary information collection

**Method Selection:**
- Numbered list of discovered methods with confidence scores
- User selects by number (1-N)
- Each method includes endpoint, authentication, documentation, and setup requirements

---

## API Reference

### Core Functions

#### `setup_gemini_client() -> tuple[genai.Client, str]`
**Purpose:** Initialise Gemini client with connectivity testing  
**Returns:** `(client, model_name)`  
**Raises:** `RuntimeError` if API key missing  
**Side Effects:** Sets environment variables, performs network test

#### `resolve_tool_from_input(client, model_name, user_text) -> dict`
**Purpose:** LLM-powered tool resolution from natural language  
**Parameters:**
- `client`: Gemini client instance
- `model_name`: Model identifier string  
- `user_text`: User's natural language tool description
**Returns:** `ToolResolution` dict with candidates array and selected_index  
**Schema Enforcement:** Uses TypedDict schema validation

#### `discover_methods_with_llm(client, model_name, candidate) -> list[OutputMethod]`
**Purpose:** LLM-powered discovery of data extraction methods  
**Parameters:**
- `candidate`: Normalised candidate dict with tool metadata
**Returns:** List of OutputMethod dicts with method_id, type, endpoints, docs  
**Error Handling:** Markdown code block extraction, JSON parsing fallbacks

### Data Structures

#### `ToolCandidate`
```python
class ToolCandidate(TypedDict):
    tool_name: str                    # "Salesforce", "HubSpot CRM"
    developer: NotRequired[str]       # "Salesforce, Inc."
    website_domain: NotRequired[str]  # "salesforce.com"
    website_url: NotRequired[str]     # "https://www.salesforce.com"
    logo_url: NotRequired[str]        # Clearbit logo URL
    confidence: NotRequired[float]    # 0.0-1.0 LLM confidence
    notes: NotRequired[str]           # Disambiguation notes
```

#### `OutputMethod`
```python
class OutputMethod(TypedDict):
    method_id: str                           # Stable hash-based identifier
    method_type: Literal["api", "mcp", "export", "webhook", "database", "connector"]
    method_name: str                         # "Salesforce REST API v1"
    endpoint: NotRequired[str]               # "https://api.salesforce.com/v1/"
    docs_url: NotRequired[str]               # Documentation link
    auth_type: NotRequired[str]              # "OAuth 2.0", "API Key"
    confidence: NotRequired[float]           # Discovery confidence
    notes: NotRequired[str]                  # Implementation notes
    setup_requirements: NotRequired[list[str]]  # Required setup steps
```

### Storage Schema

#### Intent Records (`capture-intent/index.jsonl`)
```json
{
  "id": "01K2ZFFBMHESTG7Q8CZQ54B966",
  "kind": "capture-intent",
  "version": 2,
  "created_at": "2025-08-20T14:08:33.260077+00:00",
  "source": "user-input+llm",
  "raw_input": "I need Salesforce data",
  "data": {
    "candidates": [...],
    "selected_index": 0,
    "disambiguation": "",
    "citations": []
  },
  "meta": {
    "model": "gemini-2.5-flash",
    "sdk": "google-genai"
  }
}
```

#### Method Records (`discover-methods/index.jsonl`)
```json
{
  "id": "01K33XSV5EC9MFFHPRWGWHG2JG",
  "kind": "discover-methods", 
  "version": 2,
  "created_at": "2025-08-20T14:23:21.262278+00:00",
  "source": "candidate-llm-discovery",
  "candidate_id": "salesforce-abc123def456",
  "raw_input": "Salesforce CRM",
  "data": {
    "methods": [...],
    "selected_index": 0,
    "discovery_source": "llm-powered"
  },
  "meta": {
    "notebook": "discover_methods_poc_v2.py",
    "discovery_method": "llm"
  }
}
```

---

## Advanced Configuration

### ID Generation

**Candidate IDs:**
```python
def generate_candidate_id(tool_name: str, domain: str) -> str:
    normalised_name = tool_name.lower()
    name_slug = slugify(normalised_name) or "unknown"
    hash_input = f"{normalised_name}|{domain.lower()}".encode("utf-8")
    short_hash = hashlib.sha256(hash_input).hexdigest()[:12]
    return f"{name_slug}-{short_hash}"

# Example: "salesforce-abc123def456"
```

**Method IDs:**
```python  
def generate_method_id(method_name: str, method_type: str, candidate_id: str) -> str:
    normalised_name = method_name.lower()
    name_slug = slugify(normalised_name) or "unknown"  
    hash_input = f"{normalised_name}|{method_type}|{candidate_id}".encode("utf-8")
    short_hash = hashlib.sha256(hash_input).hexdigest()[:8]
    return f"{name_slug}-{method_type}-{short_hash}"

# Example: "rest-api-api-12345678"
```

### LLM Prompt Engineering

**Tool Resolution Prompt:**
- Strict JSON schema enforcement
- Multiple candidate support with confidence ranking
- Domain validation and URL normalisation
- Disambiguation for ambiguous inputs

**Method Discovery Prompt:**
- Comprehensive method type coverage (API, MCP, Export, Webhook, Database, Connector)
- Realistic endpoint and documentation URL generation
- Authentication method specification  
- Setup requirement enumeration
- Confidence scoring based on method viability

### Error Handling Patterns

**JSON Parsing Resilience:**
```python
# Handle LLM markdown code block wrapping
text = resp.text.strip()
if text.startswith('```json\n'):
    text = text[8:]  # Remove ```json\n
if text.endswith('\n```'):
    text = text[:-4]  # Remove \n```

# Multiple fallback attempts
try:
    data = json.loads(text)
except json.JSONDecodeError:
    # Log raw response for debugging
    # Return empty list or default structure
```

**Token Limit Management:**
```python
# Progressive token limit increases
max_output_tokens=512   # Tool resolution (structured)
max_output_tokens=4096  # Method discovery (creative)

# Finish reason checking
if resp.candidates[0].finish_reason == 'MAX_TOKENS':
    # Handle truncated response
```

---

## Troubleshooting

### Common Issues

**Empty LLM Responses:**
- **Cause:** Token limits exceeded, schema constraints too strict
- **Solution:** Increase `max_output_tokens`, remove `response_schema` 
- **Debug:** Check `resp.candidates[0].finish_reason`

**JSON Parsing Errors:**
- **Cause:** LLM returns markdown-wrapped JSON  
- **Solution:** Implemented automatic code block stripping
- **Debug:** Examine `resp.text` for markdown artifacts

**Import Errors:**
- **Cause:** Missing dependencies, incorrect Python path
- **Solution:** `uv pip install` requirements, verify module structure
- **Debug:** `python -c "from capture_intent_poc_v2 import setup_gemini_client"`

**API Authentication:**
- **Cause:** Missing or invalid API key
- **Solution:** Set `GOOGLE_API_KEY` environment variable
- **Debug:** Test connectivity with minimal client setup

### Performance Optimization

**Candidate Store Lookup:**
```python  
# Avoid redundant LLM calls for known tools
existing = lookup_candidate(candidate_id)
if existing:
    return cached_resolution
```

**Batch Operations:**
```python
# Process multiple candidates simultaneously  
with ThreadPoolExecutor() as executor:
    futures = [executor.submit(discover_methods, candidate) 
              for candidate in candidates]
```

### Data Management

**Storage Cleanup:**
```bash
# Remove test records
rm discover-methods/logs/01K3*test*.json
grep -v "test" discover-methods/index.jsonl > temp && mv temp discover-methods/index.jsonl

# Archive old records  
mkdir archive/$(date +%Y%m%d)
mv discover-methods/logs/01K2*.json archive/$(date +%Y%m%d)/
```

**Schema Migration:**
```python
# Version 1 to Version 2 record upgrade
if record.get("version", 1) == 1:
    record["version"] = 2  
    record["source"] = "candidate-llm-discovery"  # Update source type
    record["data"]["discovery_source"] = "llm-powered"  # Add discovery source
```

---

## Extension Points

### Custom Method Discovery

Replace `discover_methods_with_llm()` with custom implementations:

```python
def discover_methods_custom(candidate: dict) -> list[OutputMethod]:
    # Web scraping approach
    docs_url = f"https://{candidate['website_domain']}/api/docs"
    scraped_methods = scrape_api_documentation(docs_url)
    
    # MCP registry lookup  
    mcp_servers = query_mcp_registry(candidate['tool_name'])
    
    # Combine sources
    return normalize_methods(scraped_methods + mcp_servers)
```

### Additional Storage Backends

```python
class MethodStorage:
    def persist_record(self, record: MethodRecord) -> str:
        # SQLite implementation
        cursor.execute("INSERT INTO methods VALUES (?)", [json.dumps(record)])
        
        # PostgreSQL implementation  
        cursor.execute("INSERT INTO methods (data) VALUES (%s)", [Json(record)])
        
        # Cloud storage implementation
        blob_client.upload_blob(f"methods/{record['id']}.json", json.dumps(record))
```

### Workflow Orchestration

```python
class DataExtractionWorkflow:
    def __init__(self):
        self.phases = [
            CaptureIntentPhase(),
            DiscoverMethodsPhase(), 
            CollectCredentialsPhase(),
            TestConnectionPhase(),
            ExtractDataPhase()
        ]
    
    async def execute(self, user_input: str) -> WorkflowResult:
        context = WorkflowContext(user_input=user_input)
        for phase in self.phases:
            context = await phase.execute(context)
            if not context.should_continue:
                break
        return context.result
```

---

## Next Phase Integration

The current implementation provides the foundation for **Phase 3: Credential Collection & Connection Testing**. The selected method record contains all necessary information to drive the next workflow phase:

```python
# Method record provides:
selected_method = {
    "method_type": "api",
    "auth_type": "OAuth 2.0", 
    "endpoint": "https://api.hubspot.com/",
    "docs_url": "https://developers.hubspot.com/docs/api/overview",
    "setup_requirements": [
        "Create a HubSpot developer account",
        "Create a private app to generate access token", 
        "Understand API rate limits and data models"
    ]
}

# Next phase can use this to:
# 1. Generate credential collection forms
# 2. Validate API connectivity  
# 3. Test authentication flows
# 4. Configure data extraction parameters
```

This systematic approach ensures each workflow phase has complete context from previous phases while maintaining clean separation of concerns and auditability throughout the entire data engineering pipeline.