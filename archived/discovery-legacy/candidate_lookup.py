#!/usr/bin/env python3
"""
Candidate lookup utility for discovery module.
"""

import os
import json
from typing import Optional


def lookup_candidate_by_id(candidate_id: str) -> Optional[dict]:
    """Look up candidate by ID from the capture-intent candidate store."""
    candidate_store_dir = os.path.join("data", "capture-intent", "candidates")
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
        
        return most_recent
        
    except IOError:
        return None