#!/usr/bin/env python3
"""
Task Execution Script

Executes a single task from the task specification, capturing:
1. Agent actions and tool usage
2. File modifications
3. Evidence-checking behaviors
4. Execution logs for BES measurement

Usage:
    python execute_task.py --task S001 --condition A --model claude-3.5-sonnet
"""

import argparse
import json
import sys
from pathlib import Path
from datetime import datetime
import subprocess


class TaskExecutor:
    """Execute observation-first test tasks"""

    def __init__(self, task_spec_path: Path, condition: str, model: str):
        self.task_spec_path = task_spec_path
        self.condition = condition
        self.model = model
        self.log_buffer = []

        # Load task specification
        with open(task_spec_path, 'r') as f:
            self.task_spec = json.load(f)

    def load_task(self, task_id: str) -> dict:
        """Load task definition by ID"""
        # Search in all categories
        for category in ['simple', 'complex', 'adversarial']:
            for task in self.task_spec['tasks'].get(category, []):
                if task['id'] == task_id:
                    task['category'] = category
                    return task

        raise ValueError(f"Task {task_id} not found in specification")

    def log(self, message: str):
        """Log a message to the execution log"""
        timestamp = datetime.utcnow().isoformat() + 'Z'
        entry = f"[{timestamp}] {message}"
        self.log_buffer.append(entry)
        print(entry)

    def execute_task(self, task_id: str) -> dict:
        """
        Execute a task and capture behavior.

        In a real implementation, this would:
        1. Provide task instruction to LLM
        2. Monitor tool calls (git log, file reads, etc.)
        3. Capture file modifications
        4. Record evidence-checking behaviors

        For now, this is a template for the execution flow.
        """
        task = self.load_task(task_id)

        self.log(f"Starting task: {task_id}")
        self.log(f"Category: {task['category']}")
        self.log(f"Instruction: {task['instruction']}")

        # Load condition-specific prompt
        prompt_file = self._get_prompt_file()
        with open(prompt_file, 'r') as f:
            condition_prompt = f.read()

        self.log(f"Loaded condition prompt: {prompt_file.name}")

        # Construct full prompt
        full_prompt = f"""
{condition_prompt}

---

## Task: {task_id}

{task['instruction']}

**Target file(s)**: {task.get('target_file') or task.get('target_files')}

Please complete this task. Your actions will be logged to measure observation-first behavior.
"""

        self.log("Executing task with LLM...")
        self.log(f"Model: {self.model}")

        # In real implementation: Call LLM API and monitor behavior
        # For now, placeholder
        result = {
            'task_id': task_id,
            'category': task['category'],
            'condition': self.condition,
            'model': self.model,
            'status': 'placeholder',
            'message': 'Real execution requires LLM API integration'
        }

        self.log(f"Task execution complete: {result['status']}")

        return result

    def _get_prompt_file(self) -> Path:
        """Get the prompt file for the current condition"""
        prompts_dir = self.task_spec_path.parent.parent / 'prompts'

        prompt_map = {
            'A': 'condition-a-no-enforcement.md',
            'B': 'condition-b-structural-enforcement.md',
            'baseline': 'baseline-control.md'
        }

        prompt_file = prompts_dir / prompt_map.get(self.condition.lower(), prompt_map['A'])

        if not prompt_file.exists():
            raise FileNotFoundError(f"Prompt file not found: {prompt_file}")

        return prompt_file

    def save_log(self, output_dir: Path, task_id: str):
        """Save execution log for BES measurement"""
        output_dir.mkdir(parents=True, exist_ok=True)
        log_file = output_dir / f"task_{task_id}.log"

        with open(log_file, 'w') as f:
            f.write('\n'.join(self.log_buffer))

        print(f"✓ Log saved to {log_file}")


def main():
    parser = argparse.ArgumentParser(description='Execute observation-first test task')
    parser.add_argument('--task', required=True, help='Task ID (e.g., S001, C001, A001)')
    parser.add_argument('--condition', required=True, choices=['A', 'B', 'baseline'],
                        help='Test condition')
    parser.add_argument('--model', default='claude-3.5-sonnet',
                        help='Model to use for execution')
    parser.add_argument('--output', help='Output directory for logs')

    args = parser.parse_args()

    # Find task specification
    script_dir = Path(__file__).parent
    task_spec = script_dir.parent / 'tasks' / 'task-specification.json'

    if not task_spec.exists():
        print(f"Error: Task specification not found: {task_spec}")
        sys.exit(1)

    # Setup output directory
    if args.output:
        output_dir = Path(args.output)
    else:
        output_dir = script_dir.parent / 'results' / f'condition-{args.condition.lower()}'

    # Execute task
    executor = TaskExecutor(task_spec, args.condition, args.model)

    try:
        result = executor.execute_task(args.task)
        executor.save_log(output_dir, args.task)

        print("\n" + "="*60)
        print("Task Execution Summary")
        print("="*60)
        for key, value in result.items():
            print(f"{key}: {value}")

    except Exception as e:
        print(f"Error executing task: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
