#!/usr/bin/env python3
"""
Database interface abstraction for storage operations.
Supports both DuckDB (local development) and BigQuery (production).
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Optional
from datetime import datetime


class DatabaseInterface(ABC):
    """Abstract interface for database operations."""
    
    @abstractmethod
    def store_record(self, record: Dict) -> str:
        """Store a record and return its ID."""
        pass
    
    @abstractmethod
    def get_candidate_by_id(self, candidate_id: str) -> Optional[Dict]:
        """Retrieve candidate by ID."""
        pass
    
    @abstractmethod
    def get_methods_by_candidate_id(self, candidate_id: str) -> Optional[List[Dict]]:
        """Retrieve methods by candidate ID, checking expiration."""
        pass
    
    @abstractmethod
    def health_check(self) -> bool:
        """Check database connectivity."""
        pass
    
    @abstractmethod
    def close(self) -> None:
        """Close database connection."""
        pass