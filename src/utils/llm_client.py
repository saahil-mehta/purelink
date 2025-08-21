#!/usr/bin/env python3
"""
Shared LLM client utilities for Gemini integration.
Centralises setup and common operations to eliminate duplication.
"""

import os
from google import genai
from google.genai import types


def setup_gemini_client() -> tuple[genai.Client, str]:
    """Initialise Gemini client and return client instance with model name."""
    print("=== Setting up Gemini Client ===")
    
    # CRITICAL ASSESSMENT: Hardcoded API keys pose security risk
    # BETTER ALTERNATIVE: Use environment variables or config files
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


def resolve_tool_from_input(client: genai.Client, model_name: str, user_text: str, tool_resolution_schema) -> dict:
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
            response_schema=tool_resolution_schema,
            temperature=0,  # deterministic output
            max_output_tokens=512,
        ),
    )
    
    tool_resolution = resp.parsed
    print("LLM resolution completed")
    
    # Handle case where LLM returns null/empty response
    if not tool_resolution or not isinstance(tool_resolution, dict):
        print("Warning: LLM returned empty or invalid response")
        return None
    
    return tool_resolution


def get_user_confirmation(selected_candidate: dict, auto_confirm=False) -> bool:
    """Ask user to confirm if the selected tool is correct."""
    print(f"\nSelected Tool for Confirmation:")
    print(f"   Name: {selected_candidate['tool_name']}")
    print(f"   Developer: {selected_candidate['developer'] or 'Unknown'}")
    print(f"   Domain: {selected_candidate['website_domain'] or 'Unknown'}")
    print(f"   Logo: {selected_candidate['logo_url'] or 'Not available'}")
    print(f"   Confidence: {selected_candidate['confidence']}")
    print(f"   Notes: {selected_candidate['notes']}")
    print(f"   Candidate ID: {selected_candidate['candidateId']}")
    
    if auto_confirm:
        print("\nAuto-confirming tool selection (non-interactive mode)")
        return True
    
    while True:
        confirmation = input("\nIs this the correct tool? (y/n): ").strip().lower()
        if confirmation in ['y', 'yes']:
            return True
        elif confirmation in ['n', 'no']:
            return False
        else:
            print("Please enter 'y' for yes or 'n' for no.")