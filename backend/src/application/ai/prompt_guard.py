"""Dhruva.AI V2 — Prompt Injection Defense & Safety Guardrail.

Protects against:
- Jailbreaks and role override attempts ("ignore previous instructions", "DAN mode", "system override").
- System prompt and secret extraction attempts.
- Cross-tenant data exfiltration attempts.
"""

import re
from typing import NamedTuple, Tuple


class PromptGuardVerdict(NamedTuple):
    verdict: str  # "PASS" | "FLAGGED" | "BLOCKED"
    reason: str
    risk_score: float


class PromptGuard:
    """Deterministic prompt injection and jailbreak evaluator."""

    # High severity patterns -> immediate BLOCKED
    BLOCKED_PATTERNS = [
        (re.compile(r"ignore\s+(all\s+)?(previous|prior|above)\s+(instructions|prompts|rules)", re.IGNORECASE), "Instruction Override Attempt"),
        (re.compile(r"disregard\s+(all\s+)?(safety|system|institutional)\s+(rules|guidelines|prompts)", re.IGNORECASE), "Safety Policy Bypass Attempt"),
        (re.compile(r"(reveal|print|output|show)\s+(your|the)?\s*(system\s+prompt|developer\s+instructions|secret\s+key)", re.IGNORECASE), "System Prompt Extraction Attempt"),
        (re.compile(r"(dan\s+mode|jailbreak|unrestricted\s+ai|developer\s+mode\s+enabled)", re.IGNORECASE), "Jailbreak Signature Detected"),
        (re.compile(r"(access|query|select|dump)\s+(other\s+institutions?|cross-tenant|all\s+tenants|tenants?\s+table)", re.IGNORECASE), "Cross-Tenant Exfiltration Attempt"),
        (re.compile(r"drop\s+table|insert\s+into|delete\s+from|union\s+select", re.IGNORECASE), "SQL Injection Pattern Detected"),
    ]

    # Moderate severity patterns -> FLAGGED
    FLAGGED_PATTERNS = [
        (re.compile(r"(bypass|override|disable)\s+(filter|rule|guardrail)", re.IGNORECASE), "Potential Guardrail Probe"),
        (re.compile(r"act\s+as\s+a\s+(hacker|penetration\s+tester|unfiltered)", re.IGNORECASE), "Role Manipulation Persona"),
    ]

    @classmethod
    def evaluate(cls, user_prompt: str) -> PromptGuardVerdict:
        """Evaluates a user prompt for injection or adversarial manipulation."""
        if not user_prompt or not user_prompt.strip():
            return PromptGuardVerdict(verdict="PASS", reason="Empty prompt", risk_score=0.0)

        cleaned = user_prompt.strip()

        # 1. Check critical blocked patterns
        for pattern, reason in cls.BLOCKED_PATTERNS:
            if pattern.search(cleaned):
                return PromptGuardVerdict(
                    verdict="BLOCKED",
                    reason=f"Security Guardrail: {reason}",
                    risk_score=1.0,
                )

        # 2. Check flagged patterns
        for pattern, reason in cls.FLAGGED_PATTERNS:
            if pattern.search(cleaned):
                return PromptGuardVerdict(
                    verdict="FLAGGED",
                    reason=f"Security Notice: {reason}",
                    risk_score=0.5,
                )

        return PromptGuardVerdict(
            verdict="PASS",
            reason="Prompt cleared safety checks",
            risk_score=0.0,
        )
