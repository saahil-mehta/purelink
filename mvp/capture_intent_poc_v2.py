#!/usr/bin/env python3
"""
Intent Capture POC v2 - Analysis and Findings

Overview:
This script demonstrates the intent capture workflow for identifying data tools from user input. 
The system uses Gemini to resolve natural language descriptions into structured tool information.

Key Workflow Steps:
1. Setup: Initialise Gemini client with API key
2. User Input: Capture natural language description of desired tool  
3. LLM Resolution: Use structured JSON generation to identify tool candidates
4. Post-processing: Normalise domains, generate stable IDs, populate logo URLs
5. Persistence: Store records as both individual JSON files and append-only JSONL
6. UI Payload: Generate minimal display data for frontend

Analysis from Execution:
- Input: "hibob" (HR management platform)
- Resolution: Gemini correctly identified HiBob as an HR platform with 1.0 confidence
- Output Structure: Clean JSON with candidate info, domain normalisation, and stable IDs
- Storage: Dual persistence (individual files + JSONL index) for flexibility
- Error Handling: Fixed missing hashlib import from v1

Key Improvements Made:
1. Added missing hashlib import
2. Better error handling and validation
3. Comprehensive logging and output
4. Stable candidate ID generation
5. Robust domain extraction and normalisation
"""

import os
import json  
import hashlib
from datetime import datetime, timezone
import re
import ulid
from slugify import slugify
from typing import TypedDict, NotRequired, Literal, Optional

# Import Gemini SDK
from google import genai
from google.genai import types


# Type Definitions for Structured Data
class IntentRecord(TypedDict):
    """Stable, extensible record envelope for future-proofing the append-only store."""
    id: str                                        # ULID string; unique and time-sortable
    kind: Literal["capture-intent"]                # record type tag for easy querying later
    version: int                                   # schema version for evolvability  
    created_at: str                                # RFC3339/ISO8601 UTC timestamp
    source: Literal["user-input+llm"]              # provenance tag to aid observability
    raw_input: str                                 # original user text, verbatim for traceability
    data: dict                                     # arbitrarily nested payload; schema below is a guideline
    meta: NotRequired[dict]                        # optional bag for deploy, notebook, or operator notes


class ToolCandidate(TypedDict):
    """Structured payload for tool candidate information."""
    tool_name: str                                 # canonical tool name, e.g., "Salesforce"
    developer: NotRequired[str]                    # org or vendor, e.g., "Salesforce, Inc."
    website_domain: NotRequired[str]               # bare domain, e.g., "salesforce.com" 
    website_url: NotRequired[str]                  # full URL, e.g., "https://www.salesforce.com"
    logo_url: NotRequired[str]                     # logo URL; populated via Clearbit heuristic
    confidence: NotRequired[float]                 # model-reported confidence between 0 and 1
    notes: NotRequired[str]                        # brief disambiguation notes for UX


class ToolResolution(TypedDict):
    """Complete resolution result from LLM with multiple candidates and metadata."""
    candidates: list[ToolCandidate]                # ordered best-first by the model
    selected_index: int                            # index into candidates that we will persist as "current pick" 
    disambiguation: NotRequired[str]               # short text to show the user when there's ambiguity
    citations: NotRequired[list[str]]              # optional URLs the model relied on (best-effort)


def generate_candidate_id(tool_name: str, domain: str) -> str:
    """Generate consistent candidate ID from tool name and domain."""
    normalised_name = tool_name.lower()
    name_slug = slugify(normalised_name) or "unknown"
    hash_input = f"{normalised_name}|{domain.lower()}".encode("utf-8")
    short_hash = hashlib.sha256(hash_input).hexdigest()[:12]
    return f"{name_slug}-{short_hash}"


def lookup_candidate(candidate_id: str, silent: bool = False) -> Optional[dict]:
    """Look up candidate information from the candidate store JSONL file.
    
    Args:
        candidate_id: The candidate ID to look for
        silent: If True, don't print found message (used internally)
    """
    candidate_store_dir = os.path.join("capture-intent", "candidates")
    candidates_file = os.path.join(candidate_store_dir, "candidates.jsonl")
    
    if not os.path.exists(candidates_file):
        return None
    
    try:
        # Read file backwards to get most recent version of candidate
        most_recent = None
        with open(candidates_file, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    try:
                        candidate_data = json.loads(line)
                        if candidate_data.get("candidateId") == candidate_id:
                            most_recent = candidate_data  # Keep updating to get latest
                    except json.JSONDecodeError:
                        continue
        
        if most_recent and not silent:
            print(f"Found existing candidate: {candidate_id}")
        return most_recent
        
    except IOError as e:
        print(f"Error reading candidates file: {e}")
    
    return None


def store_candidate(candidate_data: dict) -> str:
    """Store or update candidate information in the candidate store JSONL file."""
    candidate_store_dir = os.path.join("capture-intent", "candidates")
    os.makedirs(candidate_store_dir, exist_ok=True)
    candidates_file = os.path.join(candidate_store_dir, "candidates.jsonl")
    
    candidate_id = candidate_data["candidateId"]
    
    # Read all existing candidates
    existing_candidates = {}
    if os.path.exists(candidates_file):
        try:
            with open(candidates_file, "r", encoding="utf-8") as f:
                for line in f:
                    if line.strip():
                        try:
                            candidate = json.loads(line)
                            existing_candidates[candidate.get("candidateId")] = candidate
                        except json.JSONDecodeError:
                            continue
        except IOError:
            pass
    
    # Update or create candidate
    if candidate_id in existing_candidates:
        existing = existing_candidates[candidate_id]
        stored_candidate = {
            **candidate_data,
            "created_at": existing.get("created_at", datetime.now(timezone.utc).isoformat()),
            "last_accessed": datetime.now(timezone.utc).isoformat(),
            "access_count": existing.get("access_count", 0) + 1
        }
    else:
        stored_candidate = {
            **candidate_data,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "last_accessed": datetime.now(timezone.utc).isoformat(),
            "access_count": 1
        }
    
    # Update the collection
    existing_candidates[candidate_id] = stored_candidate
    
    # Write entire collection back to file (maintains uniqueness)
    with open(candidates_file, "w", encoding="utf-8") as f:
        for candidate in existing_candidates.values():
            f.write(json.dumps(candidate, ensure_ascii=False) + "\n")
    
    print(f"Stored candidate: {candidate_id}")
    return candidate_id


def resolve_from_input_with_candidate_store(user_text: str) -> Optional[dict]:
    """Resolve tool from input, checking candidate store first to avoid unnecessary LLM calls."""
    print(f"\n=== Resolving Tool from Input: '{user_text}' ===")
    
    # Search through candidate store by scanning for similar tool names
    # This is much better than hardcoded patterns - we learn from actual resolutions
    normalised_input = user_text.lower().strip()
    
    candidate_store_dir = os.path.join("capture-intent", "candidates")
    candidates_file = os.path.join(candidate_store_dir, "candidates.jsonl")
    
    if not os.path.exists(candidates_file):
        print("No candidate store found, querying LLM...")
        return None
    
    # Search through existing candidates for matches
    try:
        with open(candidates_file, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    try:
                        candidate_data = json.loads(line)
                        tool_name = candidate_data.get("tool_name", "").lower()
                        
                        # Check for exact matches or close variations
                        if (normalised_input == tool_name or 
                            normalised_input in tool_name or
                            tool_name.startswith(normalised_input) or
                            # Handle common abbreviations/misspellings
                            (len(normalised_input) >= 3 and normalised_input in tool_name)):
                            
                            print(f"Found similar candidate from store: {candidate_data.get('tool_name')}")
                            
                            return {
                                "candidates": [candidate_data],
                                "selected_index": 0,
                                "disambiguation": "",
                                "citations": [],
                                "source": "candidate-store"
                            }
                    except json.JSONDecodeError:
                        continue
    except IOError as e:
        print(f"Error reading candidates file: {e}")
    
    print("No matching candidate found in store, querying LLM...")
    return None


def setup_gemini_client() -> tuple[genai.Client, str]:
    """Initialise Gemini client and return client instance with model name."""
    print("=== Setting up Gemini Client ===")
    
    # Set API key - in production, this should come from environment variables
    # os.environ["GOOGLE_API_KEY"] = ""
    os.environ["GOOGLE_API_KEY"] = ""
    api_key = os.environ.get("GOOGLE_API_KEY") or os.environ.get("GEMINI_API_KEY")
    
    if not api_key:
        raise RuntimeError(
            "Missing API key. Set GOOGLE_API_KEY (preferred) or GEMINI_API_KEY in your environment. "
            "Create a key in Google AI Studio."
        )
    
    # Create synchronous client
    client = genai.Client(api_key=api_key)
    model_name = "gemini-2.5-flash"
    
    # Test connectivity
    response = client.models.generate_content(
        model=model_name,
        contents="Return a single short sentence confirming the client is working.",
        config=types.GenerateContentConfig(
            max_output_tokens=64,
            temperature=0.2,
        ),
    )
    
    print(f"Gemini client initialised successfully")
    print(f"Connectivity test: {response.text}")
    print(f"Using model: {model_name}")
    
    return client, model_name


def resolve_tool_from_input(client: genai.Client, model_name: str, user_text: str) -> dict:
    """Use LLM to resolve user input into structured tool information."""
    print(f"\n=== Resolving Tool from Input: '{user_text}' ===")
    
    prompt = f"""
You are a resolver that identifies a software/data tool from noisy user text.

USER_TEXT: {user_text}

Produce JSON with this structure:
{{
  "candidates": [
    {{
      "tool_name": "<canonical tool name>",
      "developer": "<vendor or developer, if known>",
      "website_domain": "<registrable domain like salesforce.com, if known>",
      "website_url": "<full homepage URL, if known>",
      "logo_url": "",  // leave empty; caller may set Clearbit-style logo from domain
      "confidence": 0.0,  // 0 to 1
      "notes": "<one-line disambiguation or clarifying note>"
    }}
  ],
  "selected_index": 0,
  "disambiguation": "<one short sentence if multiple tools are plausible>",
  "citations": []  // optional URLs if you used known references
}}

Rules:
- If multiple tools match, include the top 2-3 candidates in descending confidence and set selected_index accordingly.
- Prefer official vendor domains, not community links.
- If unsure, still return best-effort candidates and explain uncertainty in 'disambiguation'.
- Return only JSON. No extra text.
"""

    # Ask the model for strictly-typed JSON
    resp = client.models.generate_content(
        model=model_name,
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=ToolResolution,
            temperature=0,  # deterministic output
            max_output_tokens=512,
        ),
    )
    
    tool_resolution = resp.parsed
    print("LLM resolution completed")
    print("Raw LLM output:")
    print(json.dumps(tool_resolution, indent=2))
    
    # Handle case where LLM returns null/empty response
    if not tool_resolution or not isinstance(tool_resolution, dict):
        print("Warning: LLM returned empty or invalid response")
        return None
    
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
        
        # Generate deterministic candidate ID using centralised function
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
        
        # Store candidate in candidate store for future lookups
        store_candidate(normalised)
        
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
    """Persist the complete record to both individual JSON file and JSONL index."""
    print("\n=== Persisting Record ===")
    
    # Setup storage - separate logs subfolder for ULID-based records
    base_dir = "capture-intent"
    logs_dir = os.path.join(base_dir, "logs")
    os.makedirs(base_dir, exist_ok=True)
    os.makedirs(logs_dir, exist_ok=True)
    record_id = str(ulid.new())
    
    # Build structured payload
    capture_payload = {
        "candidates": normalised_candidates,
        "selected_index": selected_index,
        "disambiguation": tool_resolution.get("disambiguation", ""),
        "citations": tool_resolution.get("citations", []),
    }
    
    # Create record envelope
    record: IntentRecord = {
        "id": record_id,
        "kind": "capture-intent",
        "version": 2,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "source": "user-input+llm",
        "raw_input": user_text,
        "data": capture_payload,
        "meta": {
            "model": model_name,
            "sdk": "google-genai",
            "notebook": "capture_intent_poc_v2.py",
        },
    }
    
    # Write individual JSON file to logs subfolder
    per_record_path = os.path.join(logs_dir, f"{record_id}.json")
    with open(per_record_path, "w", encoding="utf-8") as f:
        json.dump(record, f, ensure_ascii=False, indent=2)
    
    # Keep JSONL index in main capture-intent folder
    index_path = os.path.join(base_dir, "index.jsonl")
    with open(index_path, "a", encoding="utf-8") as idx:
        idx.write(json.dumps(record, ensure_ascii=False) + "\n")
    
    print(f"Wrote record {record_id}")
    print(f"  - Individual file: {per_record_path}")
    print(f"  - JSONL index: {index_path}")
    
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
    print(json.dumps(display_payload, indent=2))
    
    return display_payload


def get_user_confirmation(selected_candidate: dict) -> bool:
    """Ask user to confirm if the selected tool is correct."""
    print(f"\nSelected Tool for Confirmation:")
    print(f"   Name: {selected_candidate['tool_name']}")
    print(f"   Developer: {selected_candidate['developer'] or 'Unknown'}")
    print(f"   Domain: {selected_candidate['website_domain'] or 'Unknown'}")
    print(f"   Logo: {selected_candidate['logo_url'] or 'Not available'}")
    print(f"   Confidence: {selected_candidate['confidence']}")
    print(f"   Notes: {selected_candidate['notes']}")
    print(f"   Candidate ID: {selected_candidate['candidateId']}")
    
    while True:
        confirmation = input("\nIs this the correct tool? (y/n): ").strip().lower()
        if confirmation in ['y', 'yes']:
            return True
        elif confirmation in ['n', 'no']:
            return False
        else:
            print("Please enter 'y' for yes or 'n' for no.")


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


def main():
    """Main execution flow for intent capture POC."""
    print("Intent Capture POC v2 - Starting")
    print("=" * 50)
    
    try:
        # 1. Setup
        client, model_name = setup_gemini_client()
        
        # Main resolution loop with retry logic
        max_retries = 3
        attempt = 0
        
        while attempt < max_retries:
            attempt += 1
            
            # 2. Get user input
            if attempt == 1:
                user_text = input("Describe the data tool you want (e.g., 'I need Salesforce customer data'): ").strip()
            else:
                print(f"\n--- Attempt {attempt} ---")
                user_text = get_supplementary_info()
            
            print(f"\nUser Input: '{user_text}'")
            
            if not user_text.strip():
                print("Please provide a short description of the tool you want.")
                continue
            
            # 3. Try candidate store first, then resolve with LLM
            tool_resolution = resolve_from_input_with_candidate_store(user_text)
            if tool_resolution is None:
                tool_resolution = resolve_tool_from_input(client, model_name, user_text)
                if tool_resolution is None:
                    print("Unable to resolve tool from input. Please try again with more specific information.")
                    continue
            
            # 4. Normalise candidates (unless already from candidate store)
            if tool_resolution.get("source") == "candidate-store":
                # Candidates from store are already normalised
                normalised_candidates = tool_resolution["candidates"]
                selected_index = tool_resolution["selected_index"]
                # Update access count for stored candidate
                for candidate in normalised_candidates:
                    if "candidateId" in candidate:
                        store_candidate(candidate)  # This will increment access count
            else:
                # New candidates from LLM need normalisation and storage
                normalised_candidates, selected_index = normalise_candidates(tool_resolution)
            
            selected_candidate = normalised_candidates[selected_index]
            
            # 5. Get user confirmation
            if get_user_confirmation(selected_candidate):
                # User confirmed - proceed with the selected tool
                break
            else:
                # User rejected - try again
                print("Let's try to find the correct tool...")
                if attempt >= max_retries:
                    print("Maximum retry attempts reached.")
                    return None
                continue
        
        # 6. Persist record
        record_id, record = persist_record(user_text, normalised_candidates, selected_index, 
                                         tool_resolution, model_name)
        
        # 7. Generate UI payload
        ui_payload = generate_ui_payload(record, selected_candidate)
        
        print(f"\nIntent Capture Complete!")
        print(f"   Record ID: {record_id}")
        print(f"   Ready for next workflow step")
        
        return {
            "record_id": record_id,
            "selected_tool": selected_candidate,
            "ui_payload": ui_payload,
            "full_record": record
        }
        
    except Exception as e:
        print(f"\nError: {e}")
        raise


if __name__ == "__main__":
    result = main()