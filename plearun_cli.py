#!/usr/bin/env python3
"""Verified Findings CLI.

Usage:
    python3 plearun_cli.py REPORT RECORDS_DIR > findings.json
"""

import json
import os
import sys

from plearun.claim_extractor import ClaimExtractor
from plearun.parsers import load_records_dir
from plearun.time_sync import ClockSynchronizer
from plearun.validator import FindingValidator
from plearun.verifier import Verifier


def run_pipeline(report_path: str, records_dir: str) -> dict:
    """Run the offline claim verification pipeline."""
    if not os.path.exists(report_path):
        print(f"Error: Report file not found: {report_path}", file=sys.stderr)
        sys.exit(1)

    if not os.path.isdir(records_dir):
        print(f"Error: Records directory not found: {records_dir}", file=sys.stderr)
        sys.exit(1)

    # 1. Parse all record sources
    records = load_records_dir(records_dir)

    # 2. Estimate clock offsets & establish time alignment
    clock_sync = ClockSynchronizer(records)

    # 3. Extract factual claims from the report narrative
    extractor = ClaimExtractor()
    claims = extractor.extract_claims(report_path)

    # 4. Reconcile evidence and formulate findings
    verifier = Verifier(records, clock_sync=clock_sync)
    raw_findings = verifier.verify_all(claims)

    # 5. Strictly validate Rule 1: quote substring check and downgrade if needed
    validator = FindingValidator(records_dir)
    final_findings = validator.validate_all(raw_findings)

    # 6. Format according to exact JSON schema
    output = {
        "findings": [f.to_dict() for f in final_findings]
    }
    return output


def main():
    if len(sys.argv) < 3:
        print("Usage: python3 plearun_cli.py REPORT RECORDS_DIR", file=sys.stderr)
        sys.exit(1)

    report_path = sys.argv[1]
    records_dir = sys.argv[2]

    result = run_pipeline(report_path, records_dir)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
