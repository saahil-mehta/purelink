#!/usr/bin/env python3
"""
Intent Capture - DuckDB Integration
Captures user intent for data tools and stores in unified DuckDB storage.
"""

import hashlib
from datetime import datetime, timezone
import re
from ulid import ULID
from slugify import slugify
from typing import TypedDict, NotRequired, Optional

# Import Gemini SDK
from google import genai

# Import shared utilities
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent / "utils"))
sys.path.append(str(Path(__file__).parent.parent / "storage"))

from llm_client import setup_gemini_client, resolve_tool_from_input as shared_resolve_tool_from_input, get_user_confirmation as shared_get_user_confirmation
from duck_store import get_database


class ToolCandidate(TypedDict):
    """Structured payload for tool candidate information."""
    candidateId: str                              # stable unique identifier
    tool_name: str                                # canonical tool name, e.g., "Salesforce"
    developer: NotRequired[str]                   # org or vendor, e.g., "Salesforce, Inc."
    website_domain: NotRequired[str]              # bare domain, e.g., "salesforce.com" 
    website_url: NotRequired[str]                 # full URL, e.g., "https://www.salesforce.com"
    logo_url: NotRequired[str]                    # logo URL; populated via Clearbit heuristic
    confidence: NotRequired[float]                # model-reported confidence between 0 and 1
    notes: NotRequired[str]                       # brief disambiguation notes for UX


class ToolResolution(TypedDict):
    """Complete resolution result from LLM with multiple candidates and metadata."""
    candidates: list[ToolCandidate]               # ordered best-first by the model
    selected_index: int                           # index into candidates that we will persist as "current pick" 
    disambiguation: NotRequired[str]              # short text to show the user when there's ambiguity
    citations: NotRequired[list[str]]             # optional URLs the model relied on (best-effort)


def generate_candidate_id(tool_name: str, domain: str) -> str:
    """Generate consistent candidate ID from tool name and domain."""
    normalised_name = tool_name.lower()
    name_slug = slugify(normalised_name) or "unknown"
    hash_input = f"{normalised_name}|{domain.lower()}".encode("utf-8")
    short_hash = hashlib.sha256(hash_input).hexdigest()[:12]
    return f"{name_slug}-{short_hash}"


def lookup_candidate_from_store(user_text: str) -> Optional[dict]:
    """Look up existing candidate from DuckDB storage based on user input."""
    print(f"\n=== Resolving Tool from Input: '{user_text}' ===")
    
    normalised_input = user_text.lower().strip()
    
    with get_database() as db:
        # Search through existing candidates for matches
        result = db.conn.execute("""
            SELECT data FROM records 
            WHERE kind = 'capture-intent'
            ORDER BY created_at DESC
        """).fetchall()
        
        for row in result:
            import json
            data = json.loads(row[0])
            
            if 'candidates' in data and 'selected_index' in data:
                candidates = data['candidates']
                selected_idx = data.get('selected_index', 0)
                
                if selected_idx < len(candidates):
                    candidate = candidates[selected_idx]
                    tool_name = candidate.get('tool_name', '').lower()
                    
                    # Check for exact matches or close variations
                    if (normalised_input == tool_name or 
                        normalised_input in tool_name or
                        tool_name.startswith(normalised_input) or
                        # Handle common abbreviations/misspellings
                        (len(normalised_input) >= 3 and normalised_input in tool_name)):
                        
                        print(f"Found similar candidate from store: {candidate.get('tool_name')}")
                        
                        return {
                            "candidates": [candidate],
                            "selected_index": 0,
                            "disambiguation": "",
                            "citations": [],
                            "source": "database-store"
                        }
    
    print("No matching candidate found in store, querying LLM...")
    return None


def resolve_tool_from_input(client: genai.Client, model_name: str, user_text: str) -> dict:
    """Use LLM to resolve user input into structured tool information."""
    tool_resolution = shared_resolve_tool_from_input(client, model_name, user_text, ToolResolution)
    
    if tool_resolution:
        print("Raw LLM output:")
        import json
        print(json.dumps(tool_resolution, indent=2))
    
    return tool_resolution


def normalise_candidates(tool_resolution: dict) -> tuple[list[dict], int]:
    """Post-process and normalise tool candidates with stable IDs and cleaned data."""
    print("\n=== Normalising Candidates ===")
    
    # Helper function for domain sanitisation
    sanitise_domain = lambda d: re.sub(r"^https?://", "", d or "").split("/")[0].lower() if d else ""
    
    normalised_candidates = []
    for i, cand in enumerate(tool_resolution.get("candidates", [])):
        print(f"Processing candidate {i+1}: {cand.get('tool_name', 'Unknown')}")
        
        # Extract and normalise fields
        domain = cand.get("website_domain") or sanitise_domain(cand.get("website_url", ""))
        domain = sanitise_domain(domain)
        logo_url = cand.get("logo_url") or (f"https://logo.clearbit.com/{domain}" if domain else "")
        tool_name = cand.get("tool_name", "").strip()
        developer = (cand.get("developer") or "").strip()
        website_url = cand.get("website_url") or (f"https://{domain}" if domain else "")
        confidence = float(cand.get("confidence", 0.0))
        notes = (cand.get("notes") or "").strip()
        
        # Generate deterministic candidate ID
        candidate_id = generate_candidate_id(tool_name, domain)
        
        normalised = {
            "candidateId": candidate_id,
            "tool_name": tool_name,
            "developer": developer,
            "website_domain": domain,
            "website_url": website_url, 
            "logo_url": logo_url,
            "confidence": confidence,
            "notes": notes,
        }
        
        normalised_candidates.append(normalised)
        
        print(f"  Generated ID: {candidate_id}")
        print(f"  Domain: {domain}")
        print(f"  Logo: {logo_url}")
    
    # Fallback for empty results
    if not normalised_candidates:
        print("No candidates returned, using fallback")
        normalised_candidates = [{
            "candidateId": "unknown-000000000000",
            "tool_name": "Unknown",
            "developer": "",
            "website_domain": "",
            "website_url": "",
            "logo_url": "",
            "confidence": 0.0,
            "notes": "No candidates returned by model",
        }]
    
    # Clamp selected index
    selected_index = int(tool_resolution.get("selected_index", 0))
    if selected_index < 0 or selected_index >= len(normalised_candidates):
        selected_index = 0
    
    print(f"Normalised {len(normalised_candidates)} candidates")
    print(f"Selected index: {selected_index}")
    
    return normalised_candidates, selected_index


def persist_record(user_text: str, normalised_candidates: list[dict], selected_index: int, 
                  tool_resolution: dict, model_name: str) -> tuple[str, dict]:
    """Persist the complete record to DuckDB."""
    print("\n=== Persisting Record ===")
    
    record_id = str(ULID())
    
    # Build structured payload
    capture_payload = {
        "candidates": normalised_candidates,
        "selected_index": selected_index,
        "selected_tool": normalised_candidates[selected_index],  # Include selected tool for easy access
        "disambiguation": tool_resolution.get("disambiguation", ""),
        "citations": tool_resolution.get("citations", []),
    }
    
    # Create record envelope
    record = {
        "id": record_id,
        "kind": "capture-intent",
        "version": 3,  # Incremented for DuckDB integration
        "created_at": datetime.now(timezone.utc).isoformat(),
        "source": "user-input+llm",
        "candidate_id": normalised_candidates[selected_index]["candidateId"],
        "raw_input": user_text,
        "data": capture_payload,
        "meta": {
            "model": model_name,
            "sdk": "google-genai",
            "storage": "duckdb",
        },
    }
    
    # Store in DuckDB
    with get_database() as db:
        stored_id = db.store_record(record)
    
    print(f"Stored record {stored_id} in DuckDB")
    
    return record_id, record


def generate_ui_payload(record: dict, selected_candidate: dict) -> dict:
    """Generate minimal payload for frontend consumption."""
    display_payload = {
        "id": record["id"],
        "tool_name": selected_candidate["tool_name"],
        "developer": selected_candidate["developer"],
        "domain": selected_candidate["website_domain"],
        "logo": selected_candidate["logo_url"],
        "disambiguation": record["data"].get("disambiguation", ""),
    }
    
    print("\n=== UI Display Payload ===")
    import json
    print(json.dumps(display_payload, indent=2))
    
    return display_payload


def get_user_confirmation(selected_candidate: dict, auto_confirm=False) -> bool:
    """Ask user to confirm if the selected tool is correct."""
    return shared_get_user_confirmation(selected_candidate, auto_confirm)


def get_supplementary_info() -> str:
    """Collect additional information from user for better tool resolution."""
    print("\nLet's gather more information to find the correct tool.")
    print("Please provide any additional details:")
    
    tool_name = input("Tool name (if different): ").strip()
    developer = input("Developer/Company name: ").strip()
    domain = input("Website domain (e.g., example.com): ").strip()
    description = input("Brief description of what the tool does: ").strip()
    
    # Build supplementary context
    parts = []
    if tool_name:
        parts.append(f"Tool name: {tool_name}")
    if developer:
        parts.append(f"Developer: {developer}")
    if domain:
        parts.append(f"Website: {domain}")
    if description:
        parts.append(f"Description: {description}")
    
    if not parts:
        return input("Please provide at least some information about the tool: ").strip()
    
    return " | ".join(parts)


def main(user_input=None, client=None, model_name=None):
    """Main execution flow for intent capture."""
    print("Intent Capture - DuckDB Integration")
    print("=" * 50)
    
    # Determine if running in non-interactive mode
    non_interactive = user_input is not None
    
    try:
        # Setup - only if not provided
        if client is None or model_name is None:
            client, model_name = setup_gemini_client()
        
        # Main resolution loop with retry logic
        max_retries = 3 if not non_interactive else 1  # Only one attempt in non-interactive mode
        attempt = 0
        
        while attempt < max_retries:
            attempt += 1
            
            # Get user input
            if attempt == 1:
                if user_input:
                    user_text = user_input.strip()
                    print(f"Using provided input: '{user_text}'")
                else:
                    user_text = input("Describe the data tool you want (e.g., 'Salesforce', 'HiBob', 'QuickBooks', 'Insta', 'FB'): ").strip()
            else:
                print(f"\n--- Attempt {attempt} ---")
                user_text = get_supplementary_info()
            
            print(f"\nUser Input: '{user_text}'")
            
            if not user_text.strip():
                print("Please provide a short description of the tool you want.")
                continue
            
            # Try database store first, then resolve with LLM
            tool_resolution = lookup_candidate_from_store(user_text)
            if tool_resolution is None:
                tool_resolution = resolve_tool_from_input(client, model_name, user_text)
                if tool_resolution is None:
                    print("Unable to resolve tool from input. Please try again with more specific information.")
                    continue
            
            # Normalise candidates (unless already from store)
            if tool_resolution.get("source") == "database-store":
                # Candidates from store are already normalised
                normalised_candidates = tool_resolution["candidates"]
                selected_index = tool_resolution["selected_index"]
            else:
                # New candidates from LLM need normalisation
                normalised_candidates, selected_index = normalise_candidates(tool_resolution)
            
            selected_candidate = normalised_candidates[selected_index]
            
            # Get user confirmation (auto-confirm in non-interactive mode)
            if get_user_confirmation(selected_candidate, auto_confirm=non_interactive):
                # User confirmed - proceed with the selected tool
                break
            else:
                # User rejected - try again
                print("Let's try to find the correct tool...")
                if attempt >= max_retries:
                    print("Maximum retry attempts reached.")
                    return None
                continue
        
        # Persist record
        record_id, record = persist_record(user_text, normalised_candidates, selected_index, 
                                         tool_resolution, model_name)
        
        # Generate UI payload
        ui_payload = generate_ui_payload(record, selected_candidate)
        
        print(f"\nIntent Capture Complete!")
        print(f"   Record ID: {record_id}")
        print(f"   Ready for next workflow step")
        
        return {
            "record_id": record_id,
            "selected_tool": selected_candidate,
            "ui_payload": ui_payload,
            "full_record": record,
            "client": client,
            "model_name": model_name
        }
        
    except Exception as e:
        print(f"\nError: {e}")
        raise


if __name__ == "__main__":
    result = main()