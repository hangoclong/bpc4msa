#!/usr/bin/env python3
"""
Helper script to update compliance rules during Experiment 5
Usage: python update_rules.py --threshold 15000
"""

import json
import argparse
import os
import time

RULES_FILE = "../config/rules.json"

def update_threshold(new_threshold):
    """Update RULE002 threshold in rules.json"""

    print(f"[{time.strftime('%H:%M:%S')}] Updating rule threshold to {new_threshold}...")

    # Read current rules
    with open(RULES_FILE, 'r') as f:
        rules = json.load(f)

    # Update RULE002
    for rule in rules:
        if rule.get('id') == 'RULE002':
            old_max = rule.get('max', 'unknown')
            rule['max'] = new_threshold
            rule['description'] = f"Transaction amount must be between 0 and {new_threshold}"
            print(f"  - Updated RULE002: max {old_max} → {new_threshold}")
            break

    # Write updated rules
    with open(RULES_FILE, 'w') as f:
        json.dump(rules, f, indent=2)

    print(f"[{time.strftime('%H:%M:%S')}] Rules updated successfully!")
    print(f"  - Compliance services will reload within 10 seconds")
    print(f"  - File: {os.path.abspath(RULES_FILE)}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Update compliance rule threshold")
    parser.add_argument('--threshold', type=int, required=True,
                        help='New maximum loan amount threshold')

    args = parser.parse_args()

    update_threshold(args.threshold)
