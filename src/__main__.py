#!/usr/bin/env python3
"""
Purelink Data Engineering Co-Pilot - Main Entry Point
Clean foundation for the EL Agent system.
"""

import argparse


def main():
    """Main entry point for the EL Agent."""
    parser = argparse.ArgumentParser(description="Purelink Data Engineering Co-Pilot")
    parser.add_argument("--source", help="Hint for data source (e.g., 'stripe', 'salesforce')")
    
    args = parser.parse_args()
    
    print("Purelink Data Engineering Co-Pilot")
    print("Clean foundation ready for EL Agent implementation")
    
    if args.source:
        print(f"Source hint provided: {args.source}")


if __name__ == "__main__":
    main()