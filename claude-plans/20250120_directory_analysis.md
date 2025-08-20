# Directory Structure Analysis - 20 January 2025

## Assessment Summary
Analysed purelink repository structure for maintainability and organisation. Found significant fragmentation undermining the POC's foundational strength.

## Key Findings
- **Duplicate structures**: `mvp/` and root both contain `capture-intent/` and `discover-methods/` directories
- **Scattered entry points**: Multiple POC files without clear canonical location
- **Mixed concerns**: Data storage, business logic, and configuration co-located
- **Security issue**: Hardcoded API keys in `mvp/capture_intent_poc_v2.py:230`
- **Empty dependencies**: `pyproject.toml` lacks required packages

## Critical Issues
1. No clear module boundaries between capture and discovery workflows
2. Archived React/TypeScript projects diluting Python POC focus  
3. Multiple documentation files without hierarchy
4. Inconsistent JSON/JSONL storage patterns

## Recommended Structure
```
src/core/ - workflow orchestration
src/capture/ - intent capture module
src/discovery/ - method discovery module  
data/ - consolidated storage
main.py - single entry point
```

## Action Required
Decide on refactoring to proposed clean structure vs accepting current fragmentation. Current code works but lacks maintainable foundation for reliable development progression.