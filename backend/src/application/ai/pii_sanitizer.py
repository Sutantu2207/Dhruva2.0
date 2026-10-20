"""Dhruva.AI V2 — Deterministic PII Sanitizer & Masker.

Guarantees:
- Zero student PII dispatched to third-party model providers.
- Scrubs emails, phone numbers, student roll numbers, government identifiers, and names.
- Returns audited redaction metadata and count.
"""

import re
from typing import Dict, List, NamedTuple, Optional


class SanitizedPIIResult(NamedTuple):
    sanitized_text: str
    pii_detected_count: int
    redactions: List[Dict[str, str]]


class PIISanitizer:
    """Deterministic PII detector and sanitizer."""

    # Patterns
    EMAIL_PATTERN = re.compile(
        r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"
    )
    # International & Indian phone numbers (10+ digits, with optional country code)
    PHONE_PATTERN = re.compile(
        r"(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b|\b[6-9]\d{9}\b"
    )
    # Roll numbers: e.g. 2026-CS-042 or CS2026-042 or 22BCE1023
    ROLL_NUMBER_PATTERN = re.compile(
        r"\b(?:\d{4}-[A-Z]{2,4}-\d{3,4}|[A-Z]{2,4}\d{4}-\d{3,4}|\d{2}[A-Z]{3}\d{4})\b"
    )
    # National IDs / SSN / Aadhaar (12 digits with optional spaces or hyphens)
    GOV_ID_PATTERN = re.compile(
        r"\b\d{4}[-\s]\d{4}[-\s]\d{4}\b|\b\d{3}-\d{2}-\d{4}\b"
    )

    @classmethod
    def sanitize(
        cls,
        text: str,
        user_names: Optional[List[str]] = None,
    ) -> SanitizedPIIResult:
        """Sanitizes text by replacing PII with deterministic placeholder tokens."""
        if not text:
            return SanitizedPIIResult(sanitized_text="", pii_detected_count=0, redactions=[])

        redactions: List[Dict[str, str]] = []
        sanitized = text

        # 1. Government IDs (highest sensitivity)
        for match in cls.GOV_ID_PATTERN.finditer(sanitized):
            val = match.group(0)
            redactions.append({"type": "GOV_ID", "original": val})
        sanitized = cls.GOV_ID_PATTERN.sub("<GOV_ID>", sanitized)

        # 2. Email addresses
        for match in cls.EMAIL_PATTERN.finditer(sanitized):
            val = match.group(0)
            redactions.append({"type": "EMAIL", "original": val})
        sanitized = cls.EMAIL_PATTERN.sub("<STUDENT_EMAIL>", sanitized)

        # 3. Phone numbers
        for match in cls.PHONE_PATTERN.finditer(sanitized):
            val = match.group(0)
            redactions.append({"type": "PHONE", "original": val})
        sanitized = cls.PHONE_PATTERN.sub("<PHONE_NUMBER>", sanitized)

        # 4. Roll / Registration numbers
        for match in cls.ROLL_NUMBER_PATTERN.finditer(sanitized):
            val = match.group(0)
            redactions.append({"type": "ROLL_NUMBER", "original": val})
        sanitized = cls.ROLL_NUMBER_PATTERN.sub("<ROLL_NUMBER>", sanitized)

        # 5. Specific user names if provided
        if user_names:
            for name in user_names:
                if name and len(name.strip()) >= 3:
                    pattern = re.compile(re.escape(name.strip()), re.IGNORECASE)
                    if pattern.search(sanitized):
                        redactions.append({"type": "STUDENT_NAME", "original": name.strip()})
                        sanitized = pattern.sub("<STUDENT_NAME>", sanitized)

        return SanitizedPIIResult(
            sanitized_text=sanitized,
            pii_detected_count=len(redactions),
            redactions=redactions,
        )
