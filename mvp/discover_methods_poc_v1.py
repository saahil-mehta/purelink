#!/usr/bin/env python3
"""
Discover Methods POC v1 - Core Component

Overview:
This script discovers available data output methods for confirmed candidate tools.
It extends the capture-intent workflow by enumerating connection options (APIs, MCP, exports).

Key Workflow Steps:
1. Input: Take candidate ID from capture-intent phase
2. Discovery: Find available output methods for that tool
3. Selection: User picks preferred method
4. Storage: Persist choice for ingestion phase

Architecture:
- Follows capture-intent patterns: ULID records, JSONL storage, TypedDict schemas
- Starts minimal: hardcoded method discovery, simple CLI selection
- Expandable: can add web scraping, API directory searches later
"""

import os
import json
import hashlib
from datetime import datetime, timezone
import ulid
from slugify import slugify
from typing import TypedDict, NotRequired, Literal, Optional

# Import Gemini for method discovery enhancement
from google import genai
from google.genai import types


# Type Definitions
class OutputMethod(TypedDict):
    """Single output method for a tool (API, MCP, export, etc.)"""
    method_id: str                      # stable identifier
    method_type: Literal["api", "mcp", "export", "webhook", "database"]
    method_name: str                    # human readable name
    endpoint: NotRequired[str]          # API endpoint or connection string
    docs_url: NotRequired[str]          # documentation link
    auth_type: NotRequired[str]         # authentication method required
    confidence: NotRequired[float]      # discovery confidence 0-1
    notes: NotRequired[str]             # implementation notes


class MethodDiscovery(TypedDict):
    """Complete method discovery result"""
    methods: list[OutputMethod]         # discovered methods
    selected_index: int                 # user's choice
    discovery_source: str               # how methods were found
    

class MethodRecord(TypedDict):
    """Storage envelope for method discovery records"""
    id: str                             # ULID
    kind: Literal["discover-methods"]   # record type
    version: int                        # schema version
    created_at: str                     # timestamp
    source: Literal["candidate-lookup"] # discovery source
    candidate_id: str                   # source candidate
    raw_input: str                      # original request
    data: MethodDiscovery               # discovery results
    meta: NotRequired[dict]             # optional metadata


def generate_method_id(method_name: str, method_type: str, candidate_id: str) -> str:
    """Generate stable method ID from name, type, and candidate."""
    normalised_name = method_name.lower()
    name_slug = slugify(normalised_name) or "unknown"
    hash_input = f"{normalised_name}|{method_type}|{candidate_id}".encode("utf-8")
    short_hash = hashlib.sha256(hash_input).hexdigest()[:8]
    return f"{name_slug}-{method_type}-{short_hash}"


def lookup_candidate(candidate_id: str) -> Optional[dict]:
    """Look up candidate information from capture-intent store."""
    candidates_file = os.path.join("mvp", "capture-intent", "candidates", "candidates.jsonl")
    
    if not os.path.exists(candidates_file):
        return None
    
    try:
        with open(candidates_file, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    candidate_data = json.loads(line)
                    if candidate_data.get("candidateId") == candidate_id:
                        return candidate_data
    except (IOError, json.JSONDecodeError):
        pass
    
    return None


def discover_methods_simple(candidate: dict) -> list[OutputMethod]:
    """Simple hardcoded method discovery - core MVP functionality."""
    tool_name = candidate.get("tool_name", "").lower()
    domain = candidate.get("website_domain", "")
    candidate_id = candidate.get("candidateId", "")
    
    methods = []
    
    # Common API patterns for well-known tools
    if "salesforce" in tool_name:
        methods.extend([
            {
                "method_id": generate_method_id("REST API", "api", candidate_id),
                "method_type": "api",
                "method_name": "Salesforce REST API",
                "endpoint": "https://developer.salesforce.com/docs/atlas.en-us.api_rest.meta/api_rest/",
                "docs_url": "https://developer.salesforce.com/docs/atlas.en-us.api_rest.meta/api_rest/",
                "auth_type": "OAuth 2.0",
                "confidence": 0.95,
                "notes": "Official REST API with comprehensive data access"
            },
            {
                "method_id": generate_method_id("SOAP API", "api", candidate_id),
                "method_type": "api", 
                "method_name": "Salesforce SOAP API",
                "endpoint": "https://developer.salesforce.com/docs/atlas.en-us.api.meta/api/",
                "docs_url": "https://developer.salesforce.com/docs/atlas.en-us.api.meta/api/",
                "auth_type": "Session ID",
                "confidence": 0.85,
                "notes": "Legacy SOAP API for complex operations"
            }
        ])
    
    elif "hubspot" in tool_name:
        methods.append({
            "method_id": generate_method_id("HubSpot API", "api", candidate_id),
            "method_type": "api",
            "method_name": "HubSpot CRM API",
            "endpoint": "https://developers.hubspot.com/docs/api/overview",
            "docs_url": "https://developers.hubspot.com/docs/api/overview", 
            "auth_type": "API Key / OAuth",
            "confidence": 0.9,
            "notes": "Modern REST API for CRM data"
        })
    
    elif "hibob" in tool_name:
        methods.extend([
            {
                "method_id": generate_method_id("HiBob API", "api", candidate_id),
                "method_type": "api",
                "method_name": "HiBob REST API",
                "endpoint": "https://apidocs.hibob.com/",
                "docs_url": "https://apidocs.hibob.com/",
                "auth_type": "Bearer Token",
                "confidence": 0.8,
                "notes": "HR platform API for employee data"
            },
            {
                "method_id": generate_method_id("CSV Export", "export", candidate_id),
                "method_type": "export",
                "method_name": "CSV Data Export",
                "docs_url": f"https://{domain}/admin/export",
                "auth_type": "Login Session",
                "confidence": 0.7,
                "notes": "Manual export via admin panel"
            }
        ])
    
    # Generic fallbacks based on domain
    if not methods and domain:
        methods.extend([
            {
                "method_id": generate_method_id("Generic API", "api", candidate_id),
                "method_type": "api",
                "method_name": f"{tool_name} API",
                "docs_url": f"https://{domain}/api/docs",
                "auth_type": "Unknown",
                "confidence": 0.3,
                "notes": "Generic API endpoint (needs verification)"
            },
            {
                "method_id": generate_method_id("Data Export", "export", candidate_id),
                "method_type": "export", 
                "method_name": "Data Export",
                "docs_url": f"https://{domain}/export",
                "auth_type": "Login Session",
                "confidence": 0.4,
                "notes": "Generic export functionality"
            }
        ])
    
    return methods


def present_methods_to_user(methods: list[OutputMethod], candidate: dict) -> int:
    """Present discovered methods to user and get selection."""
    print(f"\n=== Discovered Output Methods for {candidate.get('tool_name')} ===")
    
    if not methods:
        print("No output methods discovered for this tool.")
        return -1
    
    print(f"Found {len(methods)} available method(s):\n")
    
    for i, method in enumerate(methods):
        print(f"{i+1}. {method['method_name']} ({method['method_type'].upper()})")
        print(f"   Confidence: {method.get('confidence', 0.0):.1%}")
        if method.get('docs_url'):
            print(f"   Documentation: {method['docs_url']}")
        if method.get('auth_type'):
            print(f"   Authentication: {method['auth_type']}")
        if method.get('notes'):
            print(f"   Notes: {method['notes']}")
        print()
    
    while True:
        try:
            choice = input(f"Select method (1-{len(methods)}): ").strip()
            selected_index = int(choice) - 1
            if 0 <= selected_index < len(methods):
                return selected_index
            else:
                print(f"Please enter a number between 1 and {len(methods)}")
        except (ValueError, KeyboardInterrupt):
            print("Please enter a valid number")


def persist_method_record(candidate_id: str, methods: list[OutputMethod], 
                         selected_index: int, raw_input: str) -> tuple[str, dict]:
    """Persist method discovery record to storage."""
    print("\n=== Persisting Method Discovery ===")
    
    # Setup storage
    base_dir = "discover-methods"
    logs_dir = os.path.join(base_dir, "logs")
    os.makedirs(base_dir, exist_ok=True)
    os.makedirs(logs_dir, exist_ok=True)
    record_id = str(ulid.new())
    
    # Build discovery payload
    discovery_payload: MethodDiscovery = {
        "methods": methods,
        "selected_index": selected_index,
        "discovery_source": "hardcoded-simple"
    }
    
    # Create record envelope
    record: MethodRecord = {
        "id": record_id,
        "kind": "discover-methods",
        "version": 1,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "source": "candidate-lookup",
        "candidate_id": candidate_id,
        "raw_input": raw_input,
        "data": discovery_payload,
        "meta": {
            "notebook": "discover_methods_poc_v1.py",
            "discovery_method": "simple"
        }
    }
    
    # Write individual JSON file
    per_record_path = os.path.join(logs_dir, f"{record_id}.json")
    with open(per_record_path, "w", encoding="utf-8") as f:
        json.dump(record, f, ensure_ascii=False, indent=2)
    
    # Append to JSONL index
    index_path = os.path.join(base_dir, "index.jsonl")
    with open(index_path, "a", encoding="utf-8") as idx:
        idx.write(json.dumps(record, ensure_ascii=False) + "\n")
    
    print(f"Wrote method record {record_id}")
    print(f"  - Individual file: {per_record_path}")
    print(f"  - JSONL index: {index_path}")
    
    return record_id, record


def generate_ui_payload(record: dict, selected_method: OutputMethod) -> dict:
    """Generate minimal payload for frontend consumption."""
    display_payload = {
        "id": record["id"],
        "candidate_id": record["candidate_id"],
        "method_name": selected_method["method_name"],
        "method_type": selected_method["method_type"],
        "endpoint": selected_method.get("endpoint", ""),
        "docs_url": selected_method.get("docs_url", ""),
        "auth_type": selected_method.get("auth_type", "Unknown"),
        "confidence": selected_method.get("confidence", 0.0)
    }
    
    print("\n=== Method Selection Payload ===")
    print(json.dumps(display_payload, indent=2))
    
    return display_payload


def main(test_candidate_id: str = None):
    """Main execution flow for method discovery POC."""
    print("Discover Methods POC v1 - Starting")
    print("=" * 50)
    
    try:
        # Get candidate ID input
        if test_candidate_id:
            candidate_id = test_candidate_id
            print(f"Using test candidate ID: {candidate_id}")
        else:
            candidate_id = input("Enter candidate ID from capture-intent phase: ").strip()
        
        if not candidate_id:
            print("Please provide a candidate ID")
            return None
        
        # Look up candidate information
        print(f"\n=== Looking up candidate: {candidate_id} ===")
        candidate = lookup_candidate(candidate_id)
        
        if not candidate:
            print(f"Candidate {candidate_id} not found in capture-intent store")
            print("Make sure you've run the capture-intent POC first")
            return None
        
        print(f"Found candidate: {candidate.get('tool_name')} ({candidate.get('website_domain')})")
        
        # Discover methods
        print(f"\n=== Discovering Output Methods ===")
        methods = discover_methods_simple(candidate)
        
        if not methods:
            print("No methods discovered for this candidate")
            return None
        
        # Present options to user (or auto-select first for testing)
        if test_candidate_id and methods:
            selected_index = 0  # Auto-select first method for testing
            print(f"Auto-selecting first method for test: {methods[0]['method_name']}")
        else:
            selected_index = present_methods_to_user(methods, candidate)
            
            if selected_index == -1:
                print("No method selected")
                return None
        
        selected_method = methods[selected_index]
        print(f"\nSelected: {selected_method['method_name']}")
        
        # Persist record
        record_id, record = persist_method_record(
            candidate_id, methods, selected_index, candidate_id
        )
        
        # Generate UI payload
        ui_payload = generate_ui_payload(record, selected_method)
        
        print(f"\nMethod Discovery Complete!")
        print(f"   Record ID: {record_id}")
        print(f"   Selected Method: {selected_method['method_name']}")
        print(f"   Ready for credential collection phase")
        
        return {
            "record_id": record_id,
            "candidate_id": candidate_id,
            "selected_method": selected_method,
            "ui_payload": ui_payload,
            "full_record": record
        }
        
    except Exception as e:
        print(f"\nError: {e}")
        raise


if __name__ == "__main__":
    # Test with Slack candidate if run directly
    result = main("slack-c40ad5fab23c")