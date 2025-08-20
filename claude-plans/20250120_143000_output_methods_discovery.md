# Output Methods Discovery Plan

**Date:** 2025-01-20  
**Phase:** Post Intent-Capture → Data Output Methods Discovery  
**Status:** Awaiting Approval

## Executive Summary

The capture-intent POC is excellent and working brilliantly. The next logical step is building a discovery mechanism for available data output methods (APIs, MCP servers, Excel connectors, etc.) for confirmed candidate tools. This plan extends your existing architecture with minimal complexity while maintaining the same proven patterns.

## Critical Assessment

**What Works Well in Current System:**
- Clean separation of concerns with candidate storage
- Excellent normalisation and stable ID generation
- Robust error handling and retry logic
- Simple, testable, notebook-friendly approach

**Gap Analysis:**
- No mechanism to discover how to extract data from confirmed tools
- Missing enumeration of available connection methods
- No user selection interface for output methods
- No persistence of method choices for ingestion phase

## Recommended Approach: Simple Script Extension

**Why Simple Script (Not MCP):**
- Your current script-based approach is working exceptionally well
- MCP servers are better as output methods themselves, not discovery tools
- Maintains architectural consistency
- Keeps complexity low for POC phase
- Easier to debug and iterate

## Technical Architecture

### File Structure
```
mvp/
├── capture_intent_poc_v2.py (existing - working)
├── discover_output_methods_v1.py (new)
└── output-methods/ (new storage)
    ├── methods.jsonl (method discoveries)
    └── logs/ (individual method records)
```

### Core Workflow
1. **Input:** Confirmed candidate ID from capture-intent phase
2. **Discovery:** Enumerate available output methods for that tool
3. **Presentation:** Display options to user with confidence scores
4. **Selection:** User picks preferred method(s)
5. **Persistence:** Store selection for ingestion phase
6. **Output:** Method configuration ready for next workflow step

### Method Discovery Logic
For each confirmed candidate:
- **Official APIs:** Check for REST, GraphQL, webhooks
- **MCP Servers:** Search existing MCP registry/directory
- **Standard Exports:** CSV, Excel, database dumps
- **Third-party Connectors:** Zapier, Make.com integrations
- **Direct Database:** If applicable (internal tools)

## Detailed Implementation Plan

### Phase 1: Core Method Discovery Engine
**File:** `mvp/discover_output_methods_v1.py`

**Key Components:**
1. **Method Discovery Functions:**
   - `discover_api_methods(candidate)` - Check official API docs
   - `discover_mcp_methods(candidate)` - Search MCP registry
   - `discover_export_methods(candidate)` - Standard data exports
   - `discover_connector_methods(candidate)` - Third-party integrations

2. **Data Structures:**
   - `OutputMethod` TypedDict (method_type, endpoint, docs_url, etc.)
   - `MethodDiscovery` TypedDict (methods list, selected_index, etc.)
   - Storage format matching your existing pattern

3. **User Interface:**
   - Display discovered methods with confidence scores
   - Simple CLI selection (following your confirmation pattern)
   - Retry mechanism for unclear results

### Phase 2: Method Storage & Retrieval
**Storage Pattern:** (Following your proven approach)
- Individual JSON files with ULID in `output-methods/logs/`
- Append-only JSONL index in `output-methods/methods.jsonl`
- Method lookups by candidate ID
- Access count tracking

### Phase 3: Integration Points
**Input Integration:**
- Read confirmed candidates from `capture-intent/candidates.jsonl`
- Take candidate ID as input parameter

**Output Integration:**
- Generate method configuration for ingestion scripts
- Prepare credential collection requirements
- Set up next workflow phase inputs

## Exhaustive Todo List

### Setup & Architecture (Est: 1-2 hours)
- [ ] Create `mvp/discover_output_methods_v1.py` base structure
- [ ] Set up `output-methods/` storage directories
- [ ] Define TypedDict schemas for method discovery
- [ ] Create stable method ID generation function
- [ ] Implement basic storage functions (following candidate pattern)

### Discovery Engine Implementation (Est: 3-4 hours)
- [ ] **API Discovery Function:**
  - [ ] Check common API documentation patterns
  - [ ] Look for OpenAPI/Swagger specs
  - [ ] Identify REST vs GraphQL endpoints
  - [ ] Detect authentication requirements
  - [ ] Rate limiting information extraction

- [ ] **MCP Discovery Function:**
  - [ ] Search known MCP server registries
  - [ ] Check GitHub for tool-specific MCP implementations
  - [ ] Identify existing community MCP servers
  - [ ] Validate MCP server compatibility

- [ ] **Export Methods Discovery:**
  - [ ] Standard CSV/Excel export capabilities
  - [ ] Database dump options
  - [ ] Bulk download features
  - [ ] Scheduled export mechanisms

- [ ] **Connector Discovery:**
  - [ ] Zapier integration availability
  - [ ] Make.com connector support
  - [ ] Native integration partnerships
  - [ ] Webhook capabilities

### Method Ranking & Selection (Est: 2-3 hours)
- [ ] Implement confidence scoring for discovered methods
- [ ] Create method comparison logic (reliability, ease, completeness)
- [ ] Design user selection interface (CLI-based)
- [ ] Add method validation checks
- [ ] Implement fallback method suggestions

### User Interface & Experience (Est: 2-3 hours)
- [ ] Method presentation with clear descriptions
- [ ] Confidence indicators and recommendations
- [ ] Selection confirmation interface
- [ ] Retry mechanism for unsatisfactory results
- [ ] Help text and method explanations

### Storage & Persistence (Est: 1-2 hours)
- [ ] Method record persistence (JSONL + individual files)
- [ ] Method lookup by candidate ID
- [ ] Update existing method records
- [ ] Access tracking and usage statistics

### Integration & Testing (Est: 2-3 hours)
- [ ] Integration with existing candidate store
- [ ] End-to-end workflow testing
- [ ] Error handling and edge cases
- [ ] Validation with real candidate data
- [ ] Performance optimisation

### Documentation & Polish (Est: 1 hour)
- [ ] Code documentation and type hints
- [ ] Usage examples and test cases
- [ ] Error message clarity
- [ ] Output formatting consistency

## Success Criteria

1. **Functional Requirements:**
   - Successfully discovers 3+ methods for common tools (Salesforce, HubSpot, etc.)
   - Clean user selection interface
   - Reliable persistence matching existing pattern
   - Integration with capture-intent workflow

2. **Quality Requirements:**
   - Follows existing code patterns and style
   - Comprehensive error handling
   - Clear, actionable user feedback
   - Deterministic method IDs and storage

3. **Performance Requirements:**
   - Sub-5 second discovery for most tools
   - Graceful handling of network timeouts
   - Efficient method ranking and presentation

## Risk Assessment & Mitigation

**High Risk:**
- API discovery may fail for non-standard tools
- *Mitigation:* Fallback to manual method entry

**Medium Risk:**
- MCP registry may be incomplete
- *Mitigation:* Manual GitHub search as backup

**Low Risk:**
- Storage conflicts with existing files
- *Mitigation:* Following proven storage patterns

## Next Phase Preview

After approval and implementation:
1. **Method Configuration:** Detailed setup for selected methods
2. **Credential Collection:** Secure API key/auth gathering
3. **Connection Testing:** Validate access before data extraction
4. **Ingestion Implementation:** Actual data retrieval logic

## Timeline Estimate

**Total Implementation Time:** 12-16 hours across 3-4 working sessions
**Critical Path:** Discovery engine → User interface → Integration testing

---

**Awaiting your approval to proceed with implementation.**