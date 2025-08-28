#!/usr/bin/env python3
"""
DuckDB implementation of the database interface.
Provides efficient local storage with BigQuery-compatible patterns.
"""

import os
import json
import duckdb
from typing import List, Dict, Optional
from datetime import datetime, timezone
try:
    from .db_interface import DatabaseInterface
except ImportError:
    # Fallback for when module is run directly
    import sys
    from pathlib import Path
    sys.path.append(str(Path(__file__).parent))
    from db_interface import DatabaseInterface


class DuckDBStore(DatabaseInterface):
    """DuckDB implementation for local development storage."""
    
    def __init__(self, db_path: str = "data/purelink.duckdb"):
        """Initialize DuckDB connection and ensure schema exists."""
        # Ensure data directory exists
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        
        self.db_path = db_path
        self.conn = duckdb.connect(db_path)
        self._init_schema()
    
    def _init_schema(self) -> None:
        """Create tables if they don't exist."""
        # Create unified records table
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS records (
                id VARCHAR PRIMARY KEY,
                kind VARCHAR NOT NULL,
                candidate_id VARCHAR,
                created_at TIMESTAMP NOT NULL,
                expires_at TIMESTAMP,
                version INTEGER DEFAULT 1,
                source VARCHAR,
                raw_input TEXT,
                data JSON,
                meta JSON
            )
        """)
        
        # Create indexes separately
        self.conn.execute("CREATE INDEX IF NOT EXISTS idx_candidate_kind ON records (candidate_id, kind)")
        self.conn.execute("CREATE INDEX IF NOT EXISTS idx_expires ON records (expires_at)")
        
        # Views are not needed with the new storage approach
        # All queries go directly against the records table
    
    def store_record(self, record: Dict) -> str:
        """Store a record in the unified table."""
        # Insert record
        self.conn.execute("""
            INSERT INTO records (
                id, kind, candidate_id, created_at, expires_at, 
                version, source, raw_input, data, meta
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            record.get('id'),
            record.get('kind'),
            record.get('candidate_id'),
            record.get('created_at'),
            record.get('expires_at'),
            record.get('version', 1),
            record.get('source'),
            record.get('raw_input'),
            json.dumps(record.get('data', {})),
            json.dumps(record.get('meta', {}))
        ))
        
        return record.get('id')
    
    def get_candidate_by_id(self, candidate_id: str) -> Optional[Dict]:
        """Get most recent candidate by ID."""
        # Query records directly by candidate_id
        result = self.conn.execute("""
            SELECT data FROM records 
            WHERE kind = 'capture-intent' 
            AND candidate_id = ?
            ORDER BY created_at DESC 
            LIMIT 1
        """, (candidate_id,)).fetchone()
        
        if result:
            data = json.loads(result[0])
            # Return the selected tool from the stored data
            return data.get('selected_tool')
        
        return None
    
    def get_methods_by_candidate_id(self, candidate_id: str) -> Optional[List[Dict]]:
        """Get most recent non-expired methods by candidate ID."""
        result = self.conn.execute("""
            SELECT data FROM records 
            WHERE kind = 'discover-methods' 
            AND candidate_id = ?
            AND (expires_at IS NULL OR expires_at > CURRENT_TIMESTAMP)
            ORDER BY created_at DESC 
            LIMIT 1
        """, (candidate_id,)).fetchone()
        
        if result:
            data = json.loads(result[0])
            return data.get('methods', [])
        return None
    
    def health_check(self) -> bool:
        """Check database connectivity."""
        try:
            self.conn.execute("SELECT 1").fetchone()
            return True
        except Exception:
            return False
    
    def close(self) -> None:
        """Close database connection."""
        if hasattr(self, 'conn') and self.conn:
            self.conn.close()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


def get_database() -> DatabaseInterface:
    """Factory function to get appropriate database implementation."""
    # For now, always return DuckDB
    # In production, this would check environment variables
    return DuckDBStore()