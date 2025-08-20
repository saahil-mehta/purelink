#!/usr/bin/env python3
"""
Discover Methods POC v2 - Integrated Workflow

Overview:
This script integrates capture-intent v2 with method discovery in a seamless workflow.
Instead of hardcoded method discovery, it uses LLM to intelligently discover data output methods.

Key Workflow Steps:
1. Capture Intent: User describes tool → LLM resolves → User confirms
2. Discover Methods: Take confirmed candidate → LLM discovers output methods → User selects
3. Seamless Flow: No manual candidate ID copying, direct workflow progression

Architecture:
- Combines capture_intent_poc_v2.py functionality with intelligent method discovery
- Uses Gemini for both tool resolution AND method discovery
- Maintains same storage patterns (ULID, JSONL, individual files)
- Eliminates hardcoding through LLM-powered discovery
"""

import os
import json
import hashlib
from datetime import datetime, timezone
import ulid
from slugify import slugify
from typing import TypedDict, NotRequired, Literal, Optional

# Import Gemini SDK
from google import genai
from google.genai import types

# Import capture-intent functionality
from capture_intent_poc_v2 import (
    setup_gemini_client,
    resolve_tool_from_input,
    normalise_candidates,
    get_user_confirmation,
    generate_candidate_id,
    ToolCandidate,
    ToolResolution
)


# Method discovery types
class OutputMethod(TypedDict):
    """Single output method for a tool (API, MCP, export, etc.)"""
    method_id: str                      # stable identifier
    method_type: Literal["api", "mcp", "export", "webhook", "database", "connector"]
    method_name: str                    # human readable name
    endpoint: NotRequired[str]          # API endpoint or connection string
    docs_url: NotRequired[str]          # documentation link
    auth_type: NotRequired[str]         # authentication method required
    confidence: NotRequired[float]      # discovery confidence 0-1
    notes: NotRequired[str]             # implementation notes
    setup_requirements: NotRequired[list[str]]  # setup steps needed


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
    source: Literal["candidate-llm-discovery"] # discovery source
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




def discover_methods_with_llm(client: genai.Client, model_name: str, candidate: dict) -> list[OutputMethod]:
    """Use LLM to intelligently discover data output methods for the candidate tool."""
    print(f"\n=== Discovering Methods with LLM for {candidate['tool_name']} ===")
    
    tool_name = candidate.get("tool_name", "")
    domain = candidate.get("website_domain", "")
    developer = candidate.get("developer", "")
    candidate_id = candidate.get("candidateId", "")
    
    prompt = f"""
You are an expert in data integration who discovers available data output methods for software tools.

TOOL INFORMATION:
- Name: {tool_name}
- Developer: {developer}
- Domain: {domain}
- Website: {candidate.get('website_url', '')}

Your task is to identify realistic data extraction/output methods for this tool. Consider:
1. Official APIs (REST, GraphQL, SOAP)
2. MCP (Model Context Protocol) servers if available
3. Export features (CSV, Excel, JSON)
4. Webhooks and real-time streams
5. Database connections (if applicable)
6. Third-party connectors (Zapier, Make.com, etc.)

Produce JSON array of methods:
[
  {{
    "method_type": "api|mcp|export|webhook|database|connector",
    "method_name": "<descriptive name>",
    "endpoint": "<API endpoint or connection string if known>",
    "docs_url": "<documentation URL if exists>",
    "auth_type": "<authentication method: OAuth, API Key, Bearer Token, etc.>",
    "confidence": 0.0,
    "notes": "<implementation notes or requirements>",
    "setup_requirements": ["<list of setup steps>"]
  }}
]

Rules:
- Only suggest methods that likely exist for this specific tool
- Prefer official methods over third-party
- Include realistic documentation URLs
- Rate confidence 0.1-1.0 based on likelihood
- Provide 2-5 most viable methods
- Be specific about authentication requirements
"""

    resp = client.models.generate_content(
        model=model_name,
        contents=prompt,
        config=types.GenerateContentConfig(
            temperature=0.3,  # Slightly creative for method discovery
            max_output_tokens=4096,  # Further increased token limit
        ),
    )
    
    try:
        if not resp.text:
            print("Warning: LLM returned empty response")
            return []
        
        # Extract JSON from markdown code blocks if present
        text = resp.text.strip()
        if text.startswith('```json\n'):
            text = text[8:]  # Remove ```json\n
        if text.startswith('```\n'):
            text = text[4:]  # Remove ```\n
        if text.endswith('\n```'):
            text = text[:-4]  # Remove \n```
        if text.endswith('```'):
            text = text[:-3]  # Remove ```
            
        methods_data = json.loads(text)
        if not isinstance(methods_data, list):
            print("Warning: LLM returned non-list response, extracting methods")
            methods_data = methods_data.get("methods", []) if isinstance(methods_data, dict) else []
    except json.JSONDecodeError as e:
        print(f"Warning: Failed to parse LLM response as JSON: {e}")
        print(f"Raw response: {repr(resp.text)}")
        return []
    except Exception as e:
        print(f"Warning: Error processing LLM response: {e}")
        print(f"Response object: {resp}")
        return []
    
    # Convert to OutputMethod format with IDs
    methods = []
    for method_data in methods_data:
        if not isinstance(method_data, dict):
            continue
            
        method_name = method_data.get("method_name", "Unknown Method")
        method_type = method_data.get("method_type", "api")
        
        method: OutputMethod = {
            "method_id": generate_method_id(method_name, method_type, candidate_id),
            "method_type": method_type,
            "method_name": method_name,
            "endpoint": method_data.get("endpoint", ""),
            "docs_url": method_data.get("docs_url", ""),
            "auth_type": method_data.get("auth_type", "Unknown"),
            "confidence": float(method_data.get("confidence", 0.5)),
            "notes": method_data.get("notes", ""),
            "setup_requirements": method_data.get("setup_requirements", [])
        }
        methods.append(method)
    
    print(f"Discovered {len(methods)} methods via LLM")
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
        if method.get('endpoint'):
            print(f"   Endpoint: {method['endpoint']}")
        if method.get('notes'):
            print(f"   Notes: {method['notes']}")
        if method.get('setup_requirements'):
            print(f"   Setup: {', '.join(method['setup_requirements'][:2])}...")
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
        "discovery_source": "llm-powered"
    }
    
    # Create record envelope
    record: MethodRecord = {
        "id": record_id,
        "kind": "discover-methods",
        "version": 2,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "source": "candidate-llm-discovery",
        "candidate_id": candidate_id,
        "raw_input": raw_input,
        "data": discovery_payload,
        "meta": {
            "notebook": "discover_methods_poc_v2.py",
            "discovery_method": "llm"
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


def main():
    """Main integrated workflow: capture-intent → discover-methods."""
    print("Integrated Capture-Intent + Discover-Methods Workflow v2")
    print("=" * 60)
    
    try:
        # Setup
        client, model_name = setup_gemini_client()
        
        # === PHASE 1: CAPTURE INTENT ===
        print("\n" + "="*60)
        print("PHASE 1: CAPTURE INTENT")
        print("="*60)
        
        user_text = input("Describe the data tool you want (e.g., 'I need Salesforce customer data'): ").strip()
        
        if not user_text.strip():
            print("Please provide a tool description.")
            return None
        
        print(f"\nUser Input: '{user_text}'")
        
        # Resolve tool with LLM
        tool_resolution = resolve_tool_from_input(client, model_name, user_text)
        if tool_resolution is None:
            print("Unable to resolve tool from input.")
            return None
        
        # Normalise candidates
        normalised_candidates, selected_index = normalise_candidates(tool_resolution)
        selected_candidate = normalised_candidates[selected_index]
        
        # Get user confirmation
        if not get_user_confirmation(selected_candidate):
            print("Tool not confirmed. Exiting workflow.")
            return None
        
        print(f"\n✅ Tool confirmed: {selected_candidate['tool_name']}")
        
        # === PHASE 2: DISCOVER METHODS ===
        print("\n" + "="*60)
        print("PHASE 2: DISCOVER OUTPUT METHODS")
        print("="*60)
        
        print(f"Discovering data output methods for {selected_candidate['tool_name']}...")
        
        # LLM-powered method discovery
        methods = discover_methods_with_llm(client, model_name, selected_candidate)
        
        if not methods:
            print("No methods discovered. Workflow incomplete.")
            return None
        
        # Present methods to user
        method_index = present_methods_to_user(methods, selected_candidate)
        
        if method_index == -1:
            print("No method selected. Workflow incomplete.")
            return None
        
        selected_method = methods[method_index]
        print(f"\n✅ Method selected: {selected_method['method_name']}")
        
        # Persist method record
        record_id, record = persist_method_record(
            selected_candidate['candidateId'], 
            methods, 
            method_index, 
            user_text
        )
        
        # Generate UI payload
        ui_payload = generate_ui_payload(record, selected_method)
        
        # === WORKFLOW COMPLETE ===
        print("\n" + "="*60)
        print("WORKFLOW COMPLETE")
        print("="*60)
        
        print(f"✅ Tool: {selected_candidate['tool_name']}")
        print(f"✅ Method: {selected_method['method_name']} ({selected_method['method_type'].upper()})")
        print(f"✅ Confidence: {selected_method.get('confidence', 0.0):.1%}")
        print(f"✅ Method Record ID: {record_id}")
        
        if selected_method.get('docs_url'):
            print(f"📚 Documentation: {selected_method['docs_url']}")
        
        if selected_method.get('setup_requirements'):
            print(f"⚙️ Setup Required: {', '.join(selected_method['setup_requirements'])}")
        
        print("\n🎯 Ready for next phase: Credential Collection & Connection Testing")
        
        return {
            "candidate": selected_candidate,
            "method": selected_method,
            "method_record_id": record_id,
            "workflow_complete": True
        }
        
    except Exception as e:
        print(f"\nError in workflow: {e}")
        raise


if __name__ == "__main__":
    result = main()