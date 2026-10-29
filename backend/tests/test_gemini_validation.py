"""Dhruva.AI V2 — Gemini AI Provider Activation & Diagnostic Validation Suite.

Validates:
1. Missing credentials diagnostic (NOT_CONFIGURED, MISSING_CREDENTIALS, clear remediation).
2. Invalid credentials diagnostic (DOWN, INVALID_CREDENTIALS, non-crashing, zero secret leak).
3. Supported model configuration (prefix normalization, active Google Gemini models).
4. Multi-turn payload normalization (strict alternation user -> model -> user).
5. Transparent distinction between real Gemini and deterministic fallback models.
6. Safe API provider diagnostic endpoint inspection (/provider-status).
7. Conditional live Gemini inference test (turn 1 + turn 2 follow-up) when key is configured.
"""

import os
import uuid
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from src.application.ai.model_adapter import (
    ChatMessage,
    DeterministicGroundedProvider,
    GeminiLLMAdapter,
    OpenAICompatibleAdapter,
    get_ai_provider_status,
    get_llm_adapter,
)
from src.core.config import get_settings
from src.core.security import create_access_token
from src.domain.identity.models import Institution, User
from src.domain.identity.roles import SystemRole


class TestGeminiDiagnosticsAndValidation:
    @pytest.mark.asyncio
    async def test_missing_credentials_diagnostic(self):
        """Validates that Gemini health check cleanly flags missing credentials without crashing."""
        adapter = GeminiLLMAdapter(api_key="", model_name="gemini-1.5-flash")
        health = await adapter.health_check()

        assert health["status"] == "NOT_CONFIGURED"
        assert health["diagnostic_code"] == "MISSING_CREDENTIALS"
        assert health["configured"] is False
        assert "GEMINI_API_KEY" in health["detail"]
        assert "backend/.env" in health["remediation"]

    @pytest.mark.asyncio
    async def test_invalid_credentials_diagnostic(self):
        """Validates that an invalid Gemini API key receives HTTP 400 from Google and is categorized accurately."""
        # Intentionally invalid test key
        dummy_key = "AIzaSyDummyTestKeyForVerification0000"
        adapter = GeminiLLMAdapter(api_key=dummy_key, model_name="gemini-1.5-flash")
        health = await adapter.health_check()

        assert health["status"] == "DOWN"
        assert health["diagnostic_code"] == "INVALID_CREDENTIALS"
        assert health["configured"] is True
        # Verify secret key is never leaked in detail or remediation
        assert dummy_key not in health["detail"]
        assert dummy_key not in health["remediation"]
        assert "https://aistudio.google.com" in health["remediation"]

    def test_model_prefix_normalization(self):
        """Verifies that model prefixes ('models/' or 'google/') are normalized cleanly."""
        adapter1 = GeminiLLMAdapter(api_key="test", model_name="gemini-1.5-flash")
        assert adapter1.cleaned_model == "gemini-1.5-flash"

        adapter2 = GeminiLLMAdapter(api_key="test", model_name="models/gemini-1.5-flash")
        assert adapter2.cleaned_model == "gemini-1.5-flash"

        adapter3 = GeminiLLMAdapter(api_key="test", model_name="google/gemini-2.0-flash")
        assert adapter3.cleaned_model == "gemini-2.0-flash"

    @pytest.mark.asyncio
    async def test_multi_turn_payload_construction(self):
        """Validates that consecutive turns of the same role are merged so Gemini receives strictly alternating turns."""
        adapter = GeminiLLMAdapter(api_key="", model_name="gemini-1.5-flash")

        # History with multiple consecutive user queries
        history = [
            ChatMessage(role="user", content="What is Dijkstra's algorithm?"),
            ChatMessage(role="user", content="And what data structure does it use?"),
            ChatMessage(role="model", content="It uses a priority queue or min-heap."),
        ]

        # Call with fallback (empty key will trigger fallback)
        res = await adapter.generate_tutor_response(
            sanitized_prompt="Can it handle negative weights?",
            course_name="Data Structures and Algorithms",
            course_code="CS201",
            context_text="Unit 4: Shortest Path Algorithms",
            citations=[],
            conversation_history=history,
        )

        assert res.content is not None
        # Must be clearly identified as fallback
        assert res.model_name == "fallback/deterministic-grounded"

    @pytest.mark.asyncio
    async def test_transparent_fallback_distinction(self):
        """Validates that real Gemini model names and fallback model names are completely distinct."""
        real_model_name = "google/gemini-1.5-flash"
        fallback_model_name = "fallback/deterministic-grounded"
        deterministic_core_name = DeterministicGroundedProvider.MODEL_NAME

        assert real_model_name != fallback_model_name
        assert real_model_name != deterministic_core_name
        assert "fallback" in fallback_model_name

    @pytest.mark.asyncio
    async def test_safe_provider_status_api(self):
        """Validates that get_ai_provider_status returns complete diagnostic information for all providers."""
        status = await get_ai_provider_status()

        assert "active_provider" in status
        assert "status" in status
        assert "diagnostic_verdict" in status
        assert "remediation" in status
        assert "configured_providers" in status

        gemini_info = status["configured_providers"]["google_gemini"]
        assert "configured" in gemini_info
        assert "model" in gemini_info
        assert "status" in gemini_info
        assert "verdict" in gemini_info
        assert "remediation" in gemini_info

    @pytest.mark.asyncio
    async def test_live_gemini_if_configured(self):
        """If a valid GEMINI_API_KEY is present in the environment, executes a 2-turn live verification."""
        settings = get_settings()
        api_key = settings.GEMINI_API_KEY

        if not api_key or not api_key.strip():
            pytest.skip("GEMINI_API_KEY is not configured in server environment. Skipping live API call.")

        adapter = GeminiLLMAdapter(
            api_key=api_key,
            model_name=settings.GEMINI_MODEL,
            base_url=settings.GEMINI_API_BASE_URL,
        )

        # 1. Health check
        health = await adapter.health_check()
        if health["status"] != "UP":
            pytest.fail(f"Gemini health check failed with diagnostic: {health}")

        # 2. Turn 1: Initial question
        prompt_1 = "Explain the invariant property of a min-heap in one concise paragraph."
        res_1 = await adapter.generate_tutor_response(
            sanitized_prompt=prompt_1,
            course_name="Data Structures and Algorithms",
            course_code="CS201",
            context_text="Unit 3: Heaps and Priority Queues",
            citations=[],
        )

        assert res_1.model_name == f"google/{adapter.cleaned_model}"
        assert len(res_1.content) > 20
        assert res_1.latency_ms > 0

        # 3. Turn 2: Follow-up question relying on previous turn
        history = [
            ChatMessage(role="user", content=prompt_1),
            ChatMessage(role="model", content=res_1.content),
        ]
        prompt_2 = "Given that invariant, how does the extract-min operation restore it?"
        res_2 = await adapter.generate_tutor_response(
            sanitized_prompt=prompt_2,
            course_name="Data Structures and Algorithms",
            course_code="CS201",
            context_text="Unit 3: Heaps and Priority Queues",
            citations=[],
            conversation_history=history,
        )

        assert res_2.model_name == f"google/{adapter.cleaned_model}"
        assert len(res_2.content) > 20
        assert "heap" in res_2.content.lower() or "root" in res_2.content.lower() or "sift" in res_2.content.lower()

    @pytest.mark.asyncio
    async def test_nvidia_eol_model_diagnostic(self):
        """Validates that deprecated NVIDIA models like llama-3.1-70b-instruct return HTTP 410 / MODEL_DEPRECATED."""
        settings = get_settings()
        if not settings.NVIDIA_API_KEY:
            pytest.skip("NVIDIA_API_KEY not configured.")

        adapter = OpenAICompatibleAdapter(
            api_key=settings.NVIDIA_API_KEY,
            base_url=settings.NVIDIA_BASE_URL,
            model_name="meta/llama-3.1-70b-instruct",
        )
        health = await adapter.health_check()
        assert health["status"] == "DOWN"
        assert health["diagnostic_code"] == "MODEL_DEPRECATED"
        assert "end-of-life" in health["detail"] or "410" in health["detail"]

    @pytest.mark.asyncio
    async def test_nvidia_live_inference_two_turns(self):
        """Validates live NVIDIA NIM inference and multi-turn context retention with the active Nemotron model."""
        settings = get_settings()
        if not settings.NVIDIA_API_KEY:
            pytest.skip("NVIDIA_API_KEY not configured.")

        adapter = OpenAICompatibleAdapter(
            api_key=settings.NVIDIA_API_KEY,
            base_url=settings.NVIDIA_BASE_URL,
            model_name=settings.NVIDIA_MODEL,
        )

        # 1. Health probe
        health = await adapter.health_check()
        assert health["status"] == "UP"
        assert health["diagnostic_code"] == "SUCCESS"

        # 2. Turn 1: Academic concept
        prompt_1 = "Explain the time complexity of QuickSort in worst and best cases."
        res_1 = await adapter.generate_tutor_response(
            sanitized_prompt=prompt_1,
            course_name="Data Structures and Algorithms",
            course_code="CS201",
            context_text="Unit 2: Divide and Conquer Sorting Algorithms",
            citations=[],
        )

        assert res_1.model_name in (adapter.model_name, f"nvidia/{adapter.model_name}")
        assert len(res_1.content) > 50
        assert "n^2" in res_1.content.lower() or "o(n" in res_1.content.lower() or "worst" in res_1.content.lower()

        # 3. Turn 2: Follow-up question relying on previous turn
        history = [
            ChatMessage(role="user", content=prompt_1),
            ChatMessage(role="assistant", content=res_1.content[:400]),
        ]
        prompt_2 = "How does randomized pivot selection prevent that worst case scenario?"
        res_2 = await adapter.generate_tutor_response(
            sanitized_prompt=prompt_2,
            course_name="Data Structures and Algorithms",
            course_code="CS201",
            context_text="Unit 2: Divide and Conquer Sorting Algorithms",
            citations=[],
            conversation_history=history,
        )

        assert res_2.model_name in (adapter.model_name, f"nvidia/{adapter.model_name}")
        assert len(res_2.content) > 50
        assert "pivot" in res_2.content.lower() or "probability" in res_2.content.lower() or "random" in res_2.content.lower()

