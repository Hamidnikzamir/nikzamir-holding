#!/usr/bin/env python3
"""
BaseAgent - Mandatory Base Class for All Agents

This is the foundational law of the Nikzamir Holding codebase.
NO agent or project is allowed to execute or return a final output without
passing through the Harness (Automated Evaluation) and Loop (Self-Correction) mechanism.

Any agent script MUST inherit from this class.
"""

import sys
import os
import json
import abc

# Add project root to path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from core.harness_engine import execute_with_self_correction, MIN_HARNESS_SCORE


class BaseAgent(abc.ABC):
    """
    Abstract base class that enforces harness and loop compliance.

    Requirements:
    1. All new agents MUST inherit from this class
    2. The execute() method automatically wraps core logic with execute_with_self_correction
    3. The final payload sent to Cloudflare D1 /api/logs always includes:
       - harness_score: The harness evaluation score (0.0 to 1.0)
       - retries_used: Number of retry attempts made
    """

    def __init__(self):
        self.agent_name = self.__class__.__name__
        self.harness_score = 0.0
        self.retries_used = 0
        self.criteria = self._define_criteria()

    @abc.abstractmethod
    def _define_criteria(self):
        """
        Define the harness evaluation criteria for this agent type.
        Subclasses must implement this to return criteria string(s).
        """
        pass

    @abc.abstractmethod
    def execute_core(self):
        """
        The core logic of the agent. This is what gets wrapped
        by execute_with_self_correction.
        """
        pass

    def execute(self):
        """
        Execute the agent with mandatory harness and loop compliance.

        This method:
        1. Wraps execute_core() with execute_with_self_correction
        2. Ensures the result always includes harness_score and retries_used
        3. Returns a dict ready for Cloudflare D1 /api/logs logging

        Returns:
            dict: Result with keys:
                - success: bool
                - output: The task output
                - harness_score: Final harness evaluation score
                - retries_used: Number of retry attempts
                - failed: Whether the loop failed after max retries
        """
        print(f"\n{'=' * 60}")
        print(f"AGENT: {self.agent_name} starting execution")
        print(f"Criteria: {self.criteria}")
        print(f"{'=' * 60}\n")

        # Execute with self-correction loop (the mandatory harness)
        result = execute_with_self_correction(self.execute_core, max_retries=2)

        # Extract and store harness metrics
        self.harness_score = result.get('harness_score', 0.0)
        self.retries_used = result.get('retries_used', 0)

        # Add agent_name to the result for D1 logging
        result['agent_name'] = self.agent_name

        print(f"\n[HARNESS] Final score: {self.harness_score}")
        print(f"[HARNESS] Retries used: {self.retries_used}")
        print(f"{'=' * 60}\n")

        return result

    def log_to_d1(self, d1_client, logs_collection="logs"):
        """
        Log the agent execution results to Cloudflare D1 database.

        This must be called after execute() to persist the harness metrics.

        Args:
            d1_client: D1 database client
            logs_collection: Name of the logs collection/table
        """
        import sqlite3

        # Prepare the log entry
        log_entry = {
            'agent_name': self.agent_name,
            'harness_score': self.harness_score,
            'retries_used': self.retries_used,
            'timestamp': __import__('datetime').datetime.utcnow().isoformat() + 'Z',
            'success': result.get('success', False) if 'result' in dir() else False,
        }

        # In a real implementation, this would write to D1
        # For now, print the log entry
        print(f"[D1 LOG] Would log to {logs_collection}: {json.dumps(log_entry, indent=2)}")

        return log_entry

    def __repr__(self):
        return f"<{self.__class__.__name__} harness_score={self.harness_score} retries={self.retries_used}>"