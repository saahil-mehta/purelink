#!/usr/bin/env python3
"""
DuckDB Query Utility for Purelink
Provides easy access to query the unified database.
"""

import sys
from pathlib import Path
import json
from datetime import datetime

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

try:
    from storage.duck_store import get_database
except ImportError:
    # Fallback for direct DuckDB access
    import duckdb
    
    class DirectDB:
        def __init__(self):
            self.conn = duckdb.connect('data/purelink.duckdb')
        def __enter__(self):
            return self
        def __exit__(self, *args):
            self.conn.close()
    
    def get_database():
        return DirectDB()


def show_stats():
    """Show basic database statistics."""
    print("=== Database Statistics ===")
    
    with get_database() as db:
        # Total records
        total = db.conn.execute("SELECT COUNT(*) FROM records").fetchone()[0]
        print(f"Total records: {total}")
        
        # Records by type
        by_type = db.conn.execute("""
            SELECT kind, COUNT(*) as count 
            FROM records 
            GROUP BY kind 
            ORDER BY count DESC
        """).fetchall()
        
        for kind, count in by_type:
            print(f"  {kind}: {count}")
        
        # Unique tools
        unique_tools = db.conn.execute("""
            SELECT COUNT(DISTINCT candidate_id) 
            FROM records 
            WHERE candidate_id IS NOT NULL
        """).fetchone()[0]
        print(f"Unique tools: {unique_tools}")


def show_recent(limit=10):
    """Show recent captures."""
    print(f"\n=== Recent {limit} Captures ===")
    
    with get_database() as db:
        recent = db.conn.execute("""
            SELECT raw_input, candidate_id, created_at 
            FROM records 
            WHERE kind = 'capture-intent'
            ORDER BY created_at DESC 
            LIMIT ?
        """, (limit,)).fetchall()
        
        for raw_input, candidate_id, created_at in recent:
            timestamp = str(created_at)[:19] if created_at else 'Unknown'
            print(f"  {timestamp} | {raw_input:15} → {candidate_id}")


def show_tools():
    """Show tools by capture frequency."""
    print("\n=== Tools by Frequency ===")
    
    with get_database() as db:
        tools = db.conn.execute("""
            SELECT candidate_id, raw_input, COUNT(*) as captures,
                   MAX(created_at) as last_capture
            FROM records 
            WHERE kind = 'capture-intent' AND candidate_id IS NOT NULL
            GROUP BY candidate_id, raw_input
            ORDER BY captures DESC, last_capture DESC
        """).fetchall()
        
        for candidate_id, raw_input, captures, last_capture in tools:
            last_time = str(last_capture)[:10] if last_capture else 'Unknown'
            print(f"  {candidate_id:25} | {raw_input:10} ({captures}x, last: {last_time})")


def search_tools(query):
    """Search for tools by name or input."""
    print(f"\n=== Search Results for '{query}' ===")
    
    with get_database() as db:
        results = db.conn.execute("""
            SELECT DISTINCT candidate_id, raw_input, created_at
            FROM records 
            WHERE kind = 'capture-intent' 
            AND (raw_input ILIKE ? OR candidate_id ILIKE ?)
            ORDER BY created_at DESC
        """, (f'%{query}%', f'%{query}%')).fetchall()
        
        if results:
            for candidate_id, raw_input, created_at in results:
                timestamp = str(created_at)[:19] if created_at else 'Unknown'
                print(f"  {timestamp} | {raw_input:15} → {candidate_id}")
        else:
            print("  No matching tools found")


def show_tool_details(candidate_id):
    """Show detailed information for a specific tool."""
    print(f"\n=== Tool Details: {candidate_id} ===")
    
    with get_database() as db:
        # Get most recent capture for this tool
        result = db.conn.execute("""
            SELECT data, created_at, raw_input
            FROM records 
            WHERE kind = 'capture-intent' 
            AND candidate_id = ?
            ORDER BY created_at DESC 
            LIMIT 1
        """, (candidate_id,)).fetchone()
        
        if result:
            data, created_at, raw_input = result
            parsed_data = json.loads(data) if isinstance(data, str) else data
            
            print(f"  Last captured: {created_at}")
            print(f"  Raw input: {raw_input}")
            
            selected_tool = parsed_data.get('selected_tool', {})
            if selected_tool:
                print(f"  Tool name: {selected_tool.get('tool_name', 'Unknown')}")
                print(f"  Developer: {selected_tool.get('developer', 'Unknown')}")
                print(f"  Domain: {selected_tool.get('website_domain', 'Unknown')}")
                print(f"  Confidence: {selected_tool.get('confidence', 'Unknown')}")
                print(f"  Notes: {selected_tool.get('notes', 'None')}")
            
            # Show capture frequency
            frequency = db.conn.execute("""
                SELECT COUNT(*) 
                FROM records 
                WHERE candidate_id = ?
            """, (candidate_id,)).fetchone()[0]
            print(f"  Capture count: {frequency}")
        else:
            print("  Tool not found")


def custom_query(sql):
    """Execute custom SQL query."""
    print(f"\n=== Custom Query ===")
    print(f"SQL: {sql}")
    print("Results:")
    
    with get_database() as db:
        try:
            results = db.conn.execute(sql).fetchall()
            if results:
                for row in results:
                    print(f"  {row}")
            else:
                print("  No results")
        except Exception as e:
            print(f"  Error: {e}")


def main():
    """Main query interface."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Query Purelink DuckDB database")
    parser.add_argument('--stats', action='store_true', help='Show database statistics')
    parser.add_argument('--recent', type=int, default=10, help='Show recent captures (default: 10)')
    parser.add_argument('--tools', action='store_true', help='Show tools by frequency')
    parser.add_argument('--search', type=str, help='Search for tools by name')
    parser.add_argument('--details', type=str, help='Show details for specific candidate_id')
    parser.add_argument('--sql', type=str, help='Execute custom SQL query')
    
    args = parser.parse_args()
    
    # Default behavior: show stats and recent
    if not any([args.stats, args.tools, args.search, args.details, args.sql]):
        show_stats()
        show_recent(args.recent)
        return
    
    # Execute requested operations
    if args.stats:
        show_stats()
    
    if args.recent != 10 or not args.stats:
        show_recent(args.recent)
    
    if args.tools:
        show_tools()
    
    if args.search:
        search_tools(args.search)
    
    if args.details:
        show_tool_details(args.details)
    
    if args.sql:
        custom_query(args.sql)


if __name__ == "__main__":
    main()