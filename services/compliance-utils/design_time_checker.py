"""
Design-Time Compliance Checker
Simulates NP-complete complexity of BPM model verification

This module provides computational complexity simulation for design-time
compliance checking, which in real-world scenarios involves:
- Model checking (NP-complete)
- Temporal logic verification (PSPACE-complete)
- Path enumeration (exponential)
- Deadlock detection (polynomial but expensive)
"""

import hashlib
import time
import json
from typing import Dict, List, Any

def simulate_np_complete_work(num_activities: int) -> Dict[str, Any]:
    """
    Simulates exponential computational complexity O(2^n).

    In real BPM compliance checking, this represents:
    - Enumerating all possible execution paths
    - Model checking temporal logic properties
    - Verifying control flow constraints
    - Detecting deadlocks and unreachable states

    Args:
        num_activities: Number of activities in the process model

    Returns:
        Dict with timing information and complexity metrics
    """
    start = time.time()

    # Exponential work: 2^n iterations (capped at 2^15 for safety)
    # Real-world: checking all possible paths in process model
    iterations = 2 ** min(num_activities, 15)

    # CPU-intensive hash computation to simulate model checking
    result = 0
    for i in range(iterations):
        # Each iteration represents checking one execution path
        result ^= int(hashlib.sha256(str(i).encode()).hexdigest(), 16)

    elapsed_ms = (time.time() - start) * 1000

    return {
        'iterations': iterations,
        'complexity_class': f'O(2^{num_activities})',
        'elapsed_ms': round(elapsed_ms, 2),
        'activities_checked': num_activities,
        'paths_analyzed': iterations
    }

def check_structural_violations(process_model: Dict, rules: List[Dict]) -> List[Dict]:
    """
    Check structural compliance rules on process model.

    Structural rules include:
    - Control flow constraints (e.g., activity A must precede B)
    - Resource allocation constraints
    - Data flow constraints
    - Temporal constraints

    Complexity: O(n × m) where n=activities, m=rules
    """
    violations = []
    activities = process_model.get('activities', [])

    for rule in rules:
        if rule.get('type') != 'structural':
            continue

        rule_check_type = rule.get('check_type')

        if rule_check_type == 'ordering':
            # Check if required ordering is maintained
            before = rule.get('before_activity')
            after = rule.get('after_activity')

            if before in activities and after in activities:
                before_idx = activities.index(before)
                after_idx = activities.index(after)

                if before_idx >= after_idx:
                    violations.append({
                        'rule_id': rule.get('id'),
                        'description': rule.get('description'),
                        'violation_type': 'ordering',
                        'expected': f'{before} before {after}',
                        'actual': f'{after} at index {after_idx}, {before} at {before_idx}'
                    })

        elif rule_check_type == 'mandatory':
            # Check if mandatory activities are present
            required_activity = rule.get('activity')
            if required_activity not in activities:
                violations.append({
                    'rule_id': rule.get('id'),
                    'description': rule.get('description'),
                    'violation_type': 'missing_activity',
                    'missing': required_activity
                })

        elif rule_check_type == 'forbidden':
            # Check if forbidden activities are absent
            forbidden_activity = rule.get('activity')
            if forbidden_activity in activities:
                violations.append({
                    'rule_id': rule.get('id'),
                    'description': rule.get('description'),
                    'violation_type': 'forbidden_activity',
                    'forbidden': forbidden_activity
                })

    return violations

def design_time_compliance_check(process_model: Dict, rules: List[Dict]) -> Dict[str, Any]:
    """
    Comprehensive design-time compliance check with NP-complete simulation.

    This combines:
    1. Exponential complexity simulation (path enumeration)
    2. Structural rule checking

    Args:
        process_model: {
            'activities': ['A', 'B', 'C', ...],
            'control_flow': {...},  # optional
            'data_objects': {...}   # optional
        }
        rules: List of compliance rules

    Returns:
        {
            'violations': [...],
            'complexity_metrics': {...},
            'model_size': int,
            'check_duration_ms': float
        }
    """
    check_start = time.time()

    activities = process_model.get('activities', [])
    num_activities = len(activities)

    # Step 1: Simulate NP-complete path enumeration
    complexity_metrics = simulate_np_complete_work(num_activities)

    # Step 2: Check structural rules (linear in rules, but follows exponential work)
    structural_violations = check_structural_violations(process_model, rules)

    total_check_time = (time.time() - check_start) * 1000

    return {
        'violations': structural_violations,
        'complexity_metrics': complexity_metrics,
        'model_size': num_activities,
        'check_duration_ms': round(total_check_time, 2),
        'is_compliant': len(structural_violations) == 0
    }

def lightweight_design_check(process_model: Dict, rules: List[Dict]) -> Dict[str, Any]:
    """
    Lightweight design-time check without full path enumeration.
    Complexity: O(n × m) - polynomial time

    Use this for quick checks or small models.
    """
    check_start = time.time()

    structural_violations = check_structural_violations(process_model, rules)

    total_check_time = (time.time() - check_start) * 1000

    return {
        'violations': structural_violations,
        'model_size': len(process_model.get('activities', [])),
        'check_duration_ms': round(total_check_time, 2),
        'check_type': 'lightweight',
        'is_compliant': len(structural_violations) == 0
    }

# Example usage and testing
if __name__ == "__main__":
    # Example process model
    test_model = {
        'activities': ['Submit', 'Review', 'Approve', 'Archive', 'Notify'],
        'control_flow': {
            'Submit': ['Review'],
            'Review': ['Approve', 'Reject'],
            'Approve': ['Archive'],
            'Reject': ['Notify']
        }
    }

    # Example structural rules
    test_rules = [
        {
            'id': 'STRUCT001',
            'type': 'structural',
            'check_type': 'ordering',
            'description': 'Review must happen before Approve',
            'before_activity': 'Review',
            'after_activity': 'Approve'
        },
        {
            'id': 'STRUCT002',
            'type': 'structural',
            'check_type': 'mandatory',
            'description': 'Archive activity is mandatory',
            'activity': 'Archive'
        }
    ]

    print("=== Design-Time Compliance Check ===")
    result = design_time_compliance_check(test_model, test_rules)
    print(json.dumps(result, indent=2))

    print("\n=== Lightweight Check ===")
    lightweight_result = lightweight_design_check(test_model, test_rules)
    print(json.dumps(lightweight_result, indent=2))
