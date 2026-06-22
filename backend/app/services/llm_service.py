"""
LLM Service — Unified wrapper for OpenAI and Gemini API calls.

TIERED PROVIDER STRATEGY:
  - Ingestion pipeline  → OpenAI gpt-4o-mini  (30K RPM, cheap, reliable)
                          fallback → Gemini 2.0 Flash
  - User-facing queries → Gemini 2.0 Flash    (1M context, cheap)
                          fallback → OpenAI gpt-4o-mini

If the primary provider fails (quota / 429 / network), the fallback is tried
automatically. This means a single provider outage no longer breaks ingestion.

Usage:
    # Ingestion DNA (uses ingestion tier by default)
    result = await LLMService.generate_for_ingestion(system, user, MyModel)

    # User-facing Q&A (uses query tier by default)
    result = await LLMService.generate_for_query(system, user, MyModel)

    # Explicit provider override (legacy compatibility)
    result = await LLMService.generate(system, user, MyModel)
"""
import json
import asyncio
import logging
from typing import Any, Type
from pydantic import BaseModel
from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

# ─── Retry / timeout constants ────────────────────────────────────────────────
_GEMINI_RPM_BACKOFF_SECS = 62   # One full minute clears Gemini RPM window
_GEMINI_MAX_RETRIES       = 2   # Total attempts before giving up on Gemini
_OPENAI_MAX_RETRIES       = 2


class LLMService:
    """Unified LLM interface with tiered provider strategy and automatic fallback."""

    # ═══════════════════════════════════════════════════════
    #  PUBLIC TIER-AWARE ENTRY POINTS
    # ═══════════════════════════════════════════════════════

    @staticmethod
    async def generate_for_ingestion(
        system_prompt: str,
        user_prompt: str,
        response_model: Type[BaseModel] | None = None,
        temperature: float = 0.3,
        max_tokens: int = 2048,
    ) -> dict[str, Any] | str:
        """
        Generate a response using the ingestion-tier provider with fallback.

        Ingestion tier: OpenAI gpt-4o-mini → Gemini 2.0 Flash
        Optimized for: reliability, low latency, high rate limits.
        max_tokens defaults to 2048 — DNA and structured outputs are compact.
        """
        primary_provider   = settings.LLM_INGESTION_PROVIDER.lower()
        primary_model      = settings.LLM_INGESTION_MODEL
        fallback_provider  = "gemini" if primary_provider == "openai" else "openai"
        fallback_model     = (
            "gemini-2.0-flash" if fallback_provider == "gemini" else "gpt-4o-mini"
        )

        return await LLMService._generate_with_fallback(
            system_prompt, user_prompt, response_model, temperature, max_tokens,
            primary_provider, primary_model,
            fallback_provider, fallback_model,
            caller="ingestion",
        )

    @staticmethod
    async def generate_for_query(
        system_prompt: str,
        user_prompt: str,
        response_model: Type[BaseModel] | None = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ) -> dict[str, Any] | str:
        """
        Generate a response using the query-tier provider with fallback.

        Query tier: Gemini 2.0 Flash → OpenAI gpt-4o-mini
        Optimized for: large context windows, cost, output quality.
        """
        primary_provider   = settings.LLM_QUERY_PROVIDER.lower()
        primary_model      = settings.LLM_QUERY_MODEL
        fallback_provider  = "openai" if primary_provider == "gemini" else "gemini"
        fallback_model     = (
            "gpt-4o-mini" if fallback_provider == "openai" else "gemini-2.0-flash"
        )

        return await LLMService._generate_with_fallback(
            system_prompt, user_prompt, response_model, temperature, max_tokens,
            primary_provider, primary_model,
            fallback_provider, fallback_model,
            caller="query",
        )

    @staticmethod
    async def generate(
        system_prompt: str,
        user_prompt: str,
        response_model: Type[BaseModel] | None = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ) -> dict[str, Any] | str:
        """
        Legacy entry point — routes to the query tier by default.
        Kept for backward compatibility with mentor_engine.py calls.
        Internally calls generate_for_query.
        """
        return await LLMService.generate_for_query(
            system_prompt, user_prompt, response_model, temperature, max_tokens
        )

    # ═══════════════════════════════════════════════════════
    #  INTERNAL FALLBACK ORCHESTRATION
    # ═══════════════════════════════════════════════════════

    @staticmethod
    async def _generate_with_fallback(
        system_prompt: str,
        user_prompt: str,
        response_model: Type[BaseModel] | None,
        temperature: float,
        max_tokens: int,
        primary_provider: str,
        primary_model: str,
        fallback_provider: str,
        fallback_model: str,
        caller: str = "unknown",
    ) -> dict[str, Any] | str:
        """
        Try primary provider first; on quota/rate-limit failure, try fallback.
        Returns an error dict only if both providers fail.
        """
        # ── Primary attempt ──────────────────────────────────────────────────
        try:
            result = await LLMService._dispatch(
                provider=primary_provider,
                model=primary_model,
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                response_model=response_model,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            # A successful call returns a non-error dict or a string
            if not (isinstance(result, dict) and "error" in result):
                return result

            # Primary returned a soft error — log and try fallback
            logger.warning(
                f"[{caller}] Primary provider ({primary_provider}/{primary_model}) "
                f"returned error: {result.get('error')}. Trying fallback..."
            )
        except Exception as e:
            logger.warning(
                f"[{caller}] Primary provider ({primary_provider}/{primary_model}) "
                f"raised exception: {e}. Trying fallback..."
            )

        # ── Fallback attempt ─────────────────────────────────────────────────
        # Only attempt fallback if the key for that provider is available
        fallback_key_available = (
            (fallback_provider == "openai" and bool(settings.OPENAI_API_KEY)) or
            (fallback_provider == "gemini" and bool(settings.GEMINI_API_KEY))
        )

        if not fallback_key_available:
            logger.error(
                f"[{caller}] Fallback provider ({fallback_provider}) has no API key configured."
            )
            return {"error": f"Both providers failed. No {fallback_provider} key available.", "raw": ""}

        try:
            logger.info(
                f"[{caller}] Attempting fallback: {fallback_provider}/{fallback_model}"
            )
            result = await LLMService._dispatch(
                provider=fallback_provider,
                model=fallback_model,
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                response_model=response_model,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            if not (isinstance(result, dict) and "error" in result):
                logger.info(f"[{caller}] Fallback succeeded with {fallback_provider}/{fallback_model}")
            return result
        except Exception as e:
            logger.error(
                f"[{caller}] Fallback provider ({fallback_provider}/{fallback_model}) "
                f"also failed: {e}"
            )
            return {"error": f"Both providers failed: {str(e)[:200]}", "raw": ""}

    @staticmethod
    async def _dispatch(
        provider: str,
        model: str,
        system_prompt: str,
        user_prompt: str,
        response_model: Type[BaseModel] | None,
        temperature: float,
        max_tokens: int,
    ) -> dict[str, Any] | str:
        """Route to the correct provider implementation."""
        if provider == "openai":
            return await LLMService._generate_openai(
                system_prompt, user_prompt, response_model, temperature, max_tokens, model
            )
        elif provider == "gemini":
            return await LLMService._generate_gemini(
                system_prompt, user_prompt, response_model, temperature, max_tokens, model
            )
        else:
            raise ValueError(f"Unsupported LLM provider: {provider}")

    # ═══════════════════════════════════════════════════════
    #  PROVIDER IMPLEMENTATIONS
    # ═══════════════════════════════════════════════════════

    @staticmethod
    async def _generate_openai(
        system_prompt: str,
        user_prompt: str,
        response_model: Type[BaseModel] | None,
        temperature: float,
        max_tokens: int,
        model: str = "gpt-4o-mini",
    ) -> dict[str, Any] | str:
        """Generate response using OpenAI API with retry on transient errors."""
        from openai import AsyncOpenAI, RateLimitError, APIStatusError

        if not settings.OPENAI_API_KEY:
            return {"error": "OpenAI API key not configured", "raw": ""}

        client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        if response_model:
            schema = response_model.model_json_schema()
            messages[0]["content"] += (
                f"\n\nYou MUST respond with valid JSON matching this schema:\n"
                f"```json\n{json.dumps(schema, indent=2)}\n```\n"
                f"Respond ONLY with the JSON object, no markdown formatting."
            )

        for attempt in range(_OPENAI_MAX_RETRIES):
            try:
                response = await client.chat.completions.create(
                    model=model,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    response_format={"type": "json_object"} if response_model else None,
                )
                content = response.choices[0].message.content

                if response_model and content:
                    try:
                        return json.loads(content)
                    except json.JSONDecodeError:
                        logger.error(f"Failed to parse OpenAI JSON: {content[:200]}")
                        return {"error": "Failed to parse response", "raw": content}

                return content or ""

            except RateLimitError as e:
                if attempt < _OPENAI_MAX_RETRIES - 1:
                    wait = 10 * (attempt + 1)
                    logger.warning(f"OpenAI rate limit hit. Retrying in {wait}s... (attempt {attempt+1})")
                    await asyncio.sleep(wait)
                else:
                    logger.error(f"OpenAI rate limit — max retries reached: {e}")
                    return {"error": "OpenAI rate limit exceeded after retries", "raw": ""}

            except APIStatusError as e:
                if e.status_code == 429 and attempt < _OPENAI_MAX_RETRIES - 1:
                    wait = 10 * (attempt + 1)
                    logger.warning(f"OpenAI 429. Retrying in {wait}s...")
                    await asyncio.sleep(wait)
                else:
                    logger.error(f"OpenAI API error ({e.status_code}): {e}")
                    return {"error": f"OpenAI API error: {str(e)[:200]}", "raw": ""}

        return {"error": "OpenAI: exhausted retries", "raw": ""}

    @staticmethod
    async def _generate_gemini(
        system_prompt: str,
        user_prompt: str,
        response_model: Type[BaseModel] | None,
        temperature: float,
        max_tokens: int,
        model: str = "gemini-2.0-flash",
    ) -> dict[str, Any] | str:
        """Generate response using Google Gemini API with retry on rate limits."""
        from google import genai
        from google.genai import types
        from google.genai.errors import ClientError

        if not settings.GEMINI_API_KEY:
            return {"error": "Gemini API key not configured", "raw": ""}

        client = genai.Client(api_key=settings.GEMINI_API_KEY)

        full_prompt = user_prompt
        if response_model:
            schema = response_model.model_json_schema()
            full_prompt += (
                f"\n\nYou MUST respond with valid JSON matching this schema:\n"
                f"```json\n{json.dumps(schema, indent=2)}\n```\n"
                f"Respond ONLY with the JSON object, no markdown formatting."
            )

        for attempt in range(_GEMINI_MAX_RETRIES):
            try:
                response = await client.aio.models.generate_content(
                    model=model,
                    contents=full_prompt,
                    config=types.GenerateContentConfig(
                        system_instruction=system_prompt,
                        temperature=temperature,
                        max_output_tokens=max_tokens,
                        response_mime_type="application/json" if response_model else "text/plain",
                    ),
                )

                content = response.text

                if response_model and content:
                    try:
                        return json.loads(content)
                    except json.JSONDecodeError:
                        logger.error(f"Failed to parse Gemini JSON: {content[:200]}")
                        return {"error": "Failed to parse response", "raw": content}

                return content or ""

            except ClientError as e:
                error_msg = str(e).lower()

                # Hard quota (billing limit) — no point retrying
                if "quota" in error_msg or "billing" in error_msg:
                    logger.error(f"Gemini hard quota/billing limit: {e}")
                    return {"error": "Gemini quota exceeded", "raw": ""}

                # Rate limit (429) — back off and retry
                if e.code == 429 and attempt < _GEMINI_MAX_RETRIES - 1:
                    logger.warning(
                        f"Gemini 429 rate limit. Backing off {_GEMINI_RPM_BACKOFF_SECS}s "
                        f"(attempt {attempt + 1}/{_GEMINI_MAX_RETRIES})..."
                    )
                    await asyncio.sleep(_GEMINI_RPM_BACKOFF_SECS)
                else:
                    logger.error(f"Gemini API error (attempt {attempt + 1}): {e}")
                    if attempt == _GEMINI_MAX_RETRIES - 1:
                        return {"error": f"Gemini failed after {_GEMINI_MAX_RETRIES} attempts", "raw": ""}
                    raise

        return {"error": "Gemini: exhausted retries", "raw": ""}
