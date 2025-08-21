#!/usr/bin/env python3
"""
Purelink - Data Engineering Agent POC
Main entry point for the agent workflow orchestration.
"""

import sys
import argparse
from pathlib import Path

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from capture.intent_capture import main as capture_main
from discovery.method_discovery import main as discovery_main


def main():
    """Main orchestration for the Data Engineering Agent workflow."""
    parser = argparse.ArgumentParser(description="Purelink Data Engineering Agent")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Capture intent command
    capture_parser = subparsers.add_parser("capture", help="Capture user intent for data tools")
    capture_parser.add_argument("--input", help="Tool description input (for non-interactive mode)")
    
    # Discovery command
    discovery_parser = subparsers.add_parser("discovery", help="Discover ingestion methods for tools")
    discovery_parser.add_argument("--candidate-id", help="Candidate ID for method discovery (non-interactive mode)")
    
    # Full workflow command
    workflow_parser = subparsers.add_parser("workflow", help="Run complete capture -> discovery workflow")
    workflow_parser.add_argument("--input", help="Tool description input (for non-interactive mode)")
    workflow_parser.add_argument("--auto-confirm", action="store_true", help="Auto-confirm selections in workflow")
    
    args = parser.parse_args()
    
    if args.command == "capture":
        print("=== Starting Intent Capture Workflow ===")
        if hasattr(args, 'input') and args.input:
            # Pass input to capture_main for non-interactive mode
            return capture_main(args.input)
        else:
            return capture_main()
    elif args.command == "discovery":
        print("=== Starting Method Discovery Workflow ===")
        if hasattr(args, 'candidate_id') and args.candidate_id:
            # Pass candidate_id to discovery_main for non-interactive mode (legacy behaviour)
            return discovery_main(args.candidate_id, non_interactive=True)
        else:
            return discovery_main()
    elif args.command == "workflow":
        print("=== Starting Complete Workflow ===")
        # Always run capture interactively (maintains store lookup + confirmation)
        capture_result = capture_main()
        
        if capture_result and capture_result.get("selected_tool"):
            candidate_id = capture_result["selected_tool"]["candidateId"]
            print(f"\n=== Proceeding to Discovery Phase ===")
            print(f"Using candidate ID: {candidate_id}")
            # Reuse client from capture phase to avoid duplicate setup
            client = capture_result.get("client")
            model_name = capture_result.get("model_name")
            return discovery_main(candidate_id, non_interactive=False, client=client, model_name=model_name)
        else:
            print("Capture phase incomplete, stopping workflow")
            return None
    else:
        print("Purelink Data Engineering Agent")
        print("\nAvailable commands:")
        print("  capture   - Capture user intent for data tools")
        print("  discovery - Discover ingestion methods for tools") 
        print("  workflow  - Run complete capture -> discovery workflow")
        print("\nUse 'python main.py <command> --help' for more information")


if __name__ == "__main__":
    main()
