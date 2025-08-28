#!/usr/bin/env python3
"""
Purelink - Data Engineering Agent POC
Main entry point for the agent workflow orchestration.
"""

import sys
import argparse
from pathlib import Path
from typing import Optional, Dict, Any

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from capture.intent_capture import main as capture_main


def main() -> Optional[Dict[str, Any]]:
    """Main orchestration for the Data Engineering Agent workflow."""
    parser = argparse.ArgumentParser(description="Purelink Data Engineering Agent")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Capture intent command
    capture_parser = subparsers.add_parser("capture", help="Capture user intent for data tools")
    capture_parser.add_argument("--input", help="Tool description input (for non-interactive mode)")
    
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
    elif args.command == "workflow":
        print("=== Starting Complete Workflow ===")
        print("Note: Running capture phase with DuckDB storage integration")
        
        try:
            # Pass input to capture_main if provided
            if hasattr(args, 'input') and args.input:
                capture_result = capture_main(args.input)
            else:
                capture_result = capture_main()
            
            if capture_result and capture_result.get("selected_tool"):
                print(f"\n✅ Capture phase complete with DuckDB storage")
                print(f"Selected tool: {capture_result['selected_tool']['tool_name']}")
                print(f"Candidate ID: {capture_result['selected_tool']['candidateId']}")
                return capture_result
            else:
                print("❌ Capture phase incomplete, stopping workflow")
                return None
        except Exception as e:
            print(f"❌ Workflow error: {e}")
            return None
    else:
        print("Purelink Data Engineering Agent")
        print("\nAvailable commands:")
        print("  capture   - Capture user intent for data tools")
        print("  workflow  - Run complete capture workflow with DuckDB storage")
        print("\nUse 'python main.py <command> --help' for more information")


if __name__ == "__main__":
    main()
