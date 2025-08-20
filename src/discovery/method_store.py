#!/usr/bin/env python3
"""
Method discovery storage and retrieval utilities.
"""

import os
import json
from datetime import datetime, timezone
from typing import Optional, List


def lookup_methods_by_candidate_id(candidate_id: str) -> Optional[List[dict]]:
    """Look up previously discovered methods by candidate ID, checking expiration."""
    discover_methods_dir = os.path.join("data", "discover-methods")
    index_file = os.path.join(discover_methods_dir, "index.jsonl")
    
    if not os.path.exists(index_file):
        return None
    
    try:
        # Find most recent discovery for this candidate
        most_recent = None
        with open(index_file, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    try:
                        discovery_data = json.loads(line)
                        if discovery_data.get("candidate_id") == candidate_id:
                            most_recent = discovery_data  # Keep updating to get latest
                    except json.JSONDecodeError:
                        continue
        
        if most_recent:
            # Check if methods have expired
            data = most_recent.get("data", {})
            expires_at_str = data.get("expires_at")
            
            if expires_at_str:
                expires_at = datetime.fromisoformat(expires_at_str.replace('Z', '+00:00'))
                current_time = datetime.now(timezone.utc)
                
                if current_time > expires_at:
                    print(f"Methods for candidate {candidate_id} have expired (expired: {expires_at_str})")
                    return None  # Force LLM re-query
            
            return data.get("methods", [])
        
        return None
        
    except IOError:
        return None


def has_discovered_methods(candidate_id: str) -> bool:
    """Check if methods have already been discovered for a candidate."""
    methods = lookup_methods_by_candidate_id(candidate_id)
    return methods is not None and len(methods) > 0


def get_method_expiration_info(candidate_id: str) -> Optional[dict]:
    """Get expiration information for discovered methods."""
    discover_methods_dir = os.path.join("data", "discover-methods")
    index_file = os.path.join(discover_methods_dir, "index.jsonl")
    
    if not os.path.exists(index_file):
        return None
    
    try:
        # Find most recent discovery for this candidate
        most_recent = None
        with open(index_file, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    try:
                        discovery_data = json.loads(line)
                        if discovery_data.get("candidate_id") == candidate_id:
                            most_recent = discovery_data  # Keep updating to get latest
                    except json.JSONDecodeError:
                        continue
        
        if most_recent:
            data = most_recent.get("data", {})
            expires_at_str = data.get("expires_at")
            created_at_str = most_recent.get("created_at")
            
            if expires_at_str and created_at_str:
                expires_at = datetime.fromisoformat(expires_at_str.replace('Z', '+00:00'))
                created_at = datetime.fromisoformat(created_at_str.replace('Z', '+00:00'))
                current_time = datetime.now(timezone.utc)
                
                return {
                    "created_at": created_at_str,
                    "expires_at": expires_at_str,
                    "is_expired": current_time > expires_at,
                    "days_until_expiry": (expires_at - current_time).days if current_time <= expires_at else 0,
                    "methods_count": len(data.get("methods", []))
                }
        
        return None
        
    except IOError:
        return None