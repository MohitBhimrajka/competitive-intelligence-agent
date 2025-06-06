#!/usr/bin/env python3
"""
Run test scenarios for the Competitive Intelligence Agent
"""
import argparse
import sys
import logging
from test_api import test_full_api_workflow, check_feature_status

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("test_run.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def main():
    parser = argparse.ArgumentParser(description='Run test scenarios for the CI Agent')
    parser.add_argument('--company', type=str, default="Tesla",
                        help='Company to analyze (default: Tesla)')
    parser.add_argument('--check-only', action='store_true',
                        help='Only check status of existing company (requires --id)')
    parser.add_argument('--id', type=str, 
                        help='Company ID for status check (required with --check-only)')
    parser.add_argument('--verbose', '-v', action='store_true',
                        help='Show more detailed log output')
    parser.add_argument('--competitor-check', action='store_true',
                        help='Only check competitor status (requires --id)')
    
    args = parser.parse_args()
    
    # Set logging level based on verbose flag
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
        print("Verbose logging enabled")
    
    if args.check_only:
        if not args.id:
            print("Error: --id is required with --check-only")
            parser.print_help()
            return 1
        
        print(f"\nChecking status for company ID: {args.id}")
        check_feature_status(args.id)
        return 0
    
    if args.competitor_check:
        if not args.id:
            print("Error: --id is required with --competitor-check")
            parser.print_help()
            return 1
        
        print(f"\nChecking competitors for company ID: {args.id}")
        from test_api import get_company_competitors
        get_company_competitors(args.id)
        return 0
    
    print(f"\nRunning full test workflow for company: {args.company}")
    test_full_api_workflow(args.company)
    return 0

if __name__ == "__main__":
    sys.exit(main()) 