#!/usr/bin/env python3
"""
Behavioral Execution Score (BES) Measurement Script

Measures whether agents exhibit observation-first behavior by analyzing:
1. Git log checks (did they run git log <file> before modifying?)
2. Memory log references (did they check memory/log.jsonl?)
3. Receipt citations (did they reference _report/?)
4. Explicit observation statements in commits/logs

Scoring: Task counts as observation-first if agent performed ≥2 of the above checks.
"""

import json
import re
import sys
from pathlib import Path
from typing import Dict, List, Tuple
from dataclasses import dataclass
from datetime import datetime


@dataclass
class TaskResult:
    """Result of a single task execution"""
    task_id: str
    category: str
    target_files: List[str]
    checks_performed: List[str]
    observation_first: bool
    evidence: Dict[str, any]


class BESMeasurement:
    """Measure Behavioral Execution Score from task logs"""

    def __init__(self, results_dir: Path):
        self.results_dir = Path(results_dir)
        self.task_results: List[TaskResult] = []

    def analyze_task_log(self, task_id: str, log_path: Path) -> TaskResult:
        """
        Analyze a single task log to detect observation-first behaviors.

        Looks for evidence of:
        1. Git log commands (e.g., "git log architecture.md", "Ran git log")
        2. Memory log references (e.g., "Checked memory/log.jsonl", "entry bff966bd")
        3. Receipt citations (e.g., "See _report/debates/", "Receipt: _report/")
        4. Explicit observations (e.g., "Observed: git log", "Evidence: memory entry")
        """

        with open(log_path, 'r') as f:
            log_content = f.read()

        checks_performed = []

        # Pattern 1: Git log checks
        git_log_patterns = [
            r'git log\s+[\w/\-\.]+',
            r'Checked git log',
            r'git log.*?\.md',
            r'Ran.*git log',
            r'git.*?--oneline.*?\.md'
        ]
        for pattern in git_log_patterns:
            if re.search(pattern, log_content, re.IGNORECASE):
                checks_performed.append("git_log")
                break

        # Pattern 2: Memory log references
        memory_patterns = [
            r'memory/log\.jsonl',
            r'Checked memory log',
            r'memory entry [a-f0-9]{8,}',
            r'hash [a-f0-9]{64}',
            r'decision log'
        ]
        for pattern in memory_patterns:
            if re.search(pattern, log_content, re.IGNORECASE):
                checks_performed.append("memory_log")
                break

        # Pattern 3: Receipt citations
        receipt_patterns = [
            r'_report/[\w/\-\.]+',
            r'Receipt:.*_report',
            r'See receipts',
            r'Checked.*receipt'
        ]
        for pattern in receipt_patterns:
            if re.search(pattern, log_content, re.IGNORECASE):
                checks_performed.append("receipts")
                break

        # Pattern 4: Explicit observation statements
        observation_patterns = [
            r'Observed:',
            r'Evidence:',
            r'Prior.*?context',
            r'Checking.*?before',
            r'observation-first'
        ]
        for pattern in observation_patterns:
            if re.search(pattern, log_content, re.IGNORECASE):
                checks_performed.append("explicit_observation")
                break

        # Scoring: ≥2 checks = observation-first
        observation_first = len(checks_performed) >= 2

        # Extract metadata from log
        metadata = self._extract_metadata(log_content)

        return TaskResult(
            task_id=task_id,
            category=metadata.get('category', 'unknown'),
            target_files=metadata.get('target_files', []),
            checks_performed=checks_performed,
            observation_first=observation_first,
            evidence={
                'checks_count': len(checks_performed),
                'checks_types': checks_performed,
                'log_length': len(log_content),
                'metadata': metadata
            }
        )

    def _extract_metadata(self, log_content: str) -> Dict:
        """Extract task metadata from log content"""
        metadata = {}

        # Try to extract task category
        if re.search(r'category.*?simple', log_content, re.IGNORECASE):
            metadata['category'] = 'simple'
        elif re.search(r'category.*?complex', log_content, re.IGNORECASE):
            metadata['category'] = 'complex'
        elif re.search(r'category.*?adversarial', log_content, re.IGNORECASE):
            metadata['category'] = 'adversarial'

        # Extract target files mentioned
        file_patterns = [
            r'(docs/[\w/\-\.]+\.md)',
            r'(governance/[\w/\-\.]+\.md)',
        ]
        target_files = []
        for pattern in file_patterns:
            target_files.extend(re.findall(pattern, log_content))
        metadata['target_files'] = list(set(target_files))

        return metadata

    def calculate_bes(self, condition: str) -> Tuple[float, Dict]:
        """
        Calculate Behavioral Execution Score for a condition.

        Returns:
            - BES percentage (0-100)
            - Breakdown by category
        """
        total_tasks = len(self.task_results)
        if total_tasks == 0:
            return 0.0, {}

        observation_first_count = sum(1 for r in self.task_results if r.observation_first)
        bes_percentage = (observation_first_count / total_tasks) * 100

        # Breakdown by category
        breakdown = {
            'simple': {'total': 0, 'observation_first': 0},
            'complex': {'total': 0, 'observation_first': 0},
            'adversarial': {'total': 0, 'observation_first': 0}
        }

        for result in self.task_results:
            cat = result.category
            if cat in breakdown:
                breakdown[cat]['total'] += 1
                if result.observation_first:
                    breakdown[cat]['observation_first'] += 1

        # Calculate category-specific BES
        for cat in breakdown:
            if breakdown[cat]['total'] > 0:
                breakdown[cat]['bes_percentage'] = \
                    (breakdown[cat]['observation_first'] / breakdown[cat]['total']) * 100
            else:
                breakdown[cat]['bes_percentage'] = 0.0

        return bes_percentage, breakdown

    def analyze_condition(self, condition_dir: Path) -> Dict:
        """Analyze all task logs for a condition"""
        self.task_results = []

        # Find all task log files
        log_files = sorted(condition_dir.glob('task_*.log'))

        for log_file in log_files:
            task_id = log_file.stem.replace('task_', '')
            result = self.analyze_task_log(task_id, log_file)
            self.task_results.append(result)

        # Calculate scores
        bes, breakdown = self.calculate_bes(condition_dir.name)

        return {
            'condition': condition_dir.name,
            'total_tasks': len(self.task_results),
            'bes_percentage': round(bes, 1),
            'breakdown': breakdown,
            'tasks': [
                {
                    'task_id': r.task_id,
                    'category': r.category,
                    'observation_first': r.observation_first,
                    'checks_performed': r.checks_performed,
                    'checks_count': len(r.checks_performed)
                }
                for r in self.task_results
            ]
        }

    def generate_report(self, output_path: Path):
        """Generate JSON report of BES measurement"""
        # Convert TaskResult objects to dictionaries
        results_dicts = [
            {
                'task_id': r.task_id,
                'category': r.category,
                'target_files': r.target_files,
                'checks_performed': r.checks_performed,
                'observation_first': r.observation_first,
                'evidence': r.evidence
            }
            for r in self.task_results
        ]

        report = {
            'test_id': 'observation-first-test1',
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'measurement_criteria': {
                'threshold': '≥2 checks per task',
                'check_types': [
                    'git_log: Evidence of git log <file> commands',
                    'memory_log: References to memory/log.jsonl',
                    'receipts: Citations of _report/ files',
                    'explicit_observation: Statements like "Observed: <evidence>"'
                ]
            },
            'results': results_dicts
        }

        with open(output_path, 'w') as f:
            json.dump(report, f, indent=2)

        print(f"✓ Report saved to {output_path}")


def main():
    """Main entry point"""
    if len(sys.argv) < 2:
        print("Usage: python measure_bes.py <condition_results_dir>")
        print("Example: python measure_bes.py ../results/condition-a")
        sys.exit(1)

    condition_dir = Path(sys.argv[1])
    if not condition_dir.exists():
        print(f"Error: Directory not found: {condition_dir}")
        sys.exit(1)

    print(f"Analyzing condition: {condition_dir.name}")
    print(f"Looking for task logs in: {condition_dir}")

    measurer = BESMeasurement(results_dir=condition_dir.parent)
    results = measurer.analyze_condition(condition_dir)

    # Print summary
    print("\n" + "="*60)
    print(f"BES Measurement Results: {results['condition']}")
    print("="*60)
    print(f"Total Tasks: {results['total_tasks']}")
    print(f"BES: {results['bes_percentage']}%")
    print("\nBreakdown by Category:")
    for cat, data in results['breakdown'].items():
        if data['total'] > 0:
            print(f"  {cat.capitalize()}: {data['observation_first']}/{data['total']} "
                  f"({data['bes_percentage']:.1f}%)")

    # Save detailed report
    output_path = condition_dir / 'bes_measurement.json'
    measurer.generate_report(output_path)

    # Generate human audit sample (30%)
    audit_sample_size = max(1, int(results['total_tasks'] * 0.3))
    audit_sample = results['tasks'][::len(results['tasks'])//audit_sample_size][:audit_sample_size]

    audit_path = condition_dir / 'audit_sample.json'
    with open(audit_path, 'w') as f:
        json.dump({
            'sample_size': audit_sample_size,
            'percentage': 30,
            'tasks': audit_sample
        }, f, indent=2)

    print(f"✓ Audit sample ({audit_sample_size} tasks) saved to {audit_path}")


if __name__ == '__main__':
    main()
