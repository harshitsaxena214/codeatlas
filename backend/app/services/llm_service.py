"""
LLM Service — Unified wrapper for OpenAI, Gemini, Groq, and OpenRouter API calls.

TIERED PROVIDER STRATEGY:
  - Ingestion pipeline  → primary (config)  → secondary  → Groq  → OpenRouter
  - User-facing queries → primary (config)  → secondary  → Groq  → OpenRouter

If the primary provider fails (quota / 429 / network), the secondary is tried,
then Groq and OpenRouter as successive tiers (if keys are
configured). This means a single provider outage no longer breaks ingestion.

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
_GROQ_MAX_RETRIES         = 2
_OPENROUTER_MAX_RETRIES   = 2


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
        # Secondary selection
        if primary_provider == "openai":
            fallback_provider, fallback_model = "gemini", "gemini-2.5-flash"
        elif primary_provider == "gemini":
            fallback_provider, fallback_model = "openai", "gpt-4o-mini"
        elif primary_provider == "groq":
            fallback_provider, fallback_model = "openai", "gpt-4o-mini"
        else:  # openrouter or other
            fallback_provider, fallback_model = "gemini", "gemini-2.5-flash"

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
        # Secondary selection
        if primary_provider == "gemini":
            fallback_provider, fallback_model = "openai", "gpt-4o-mini"
        elif primary_provider == "openai":
            fallback_provider, fallback_model = "gemini", "gemini-2.5-flash"
        elif primary_provider == "groq":
            fallback_provider, fallback_model = "gemini", "gemini-2.5-flash"
        else:  # openrouter or other
            fallback_provider, fallback_model = "gemini", "gemini-2.5-flash"

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
        Try primary provider first; on quota/rate-limit failure, try secondary,
        then Groq and OpenRouter as final tiers (if keys are configured).
        Uses a `tried` set so no provider is retried and guards work correctly
        regardless of which provider is primary.
        Returns an error dict only if all providers fail.
        """
        tried: set[str] = {primary_provider}
        last_error: str = "no providers configured"

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
            last_error = result.get("error", "unknown")
            logger.warning(
                f"[{caller}] Primary provider ({primary_provider}/{primary_model}) "
                f"returned error: {last_error}. Trying fallback..."
            )
        except Exception as e:
            last_error = str(e)
            logger.warning(
                f"[{caller}] Primary provider ({primary_provider}/{primary_model}) "
                f"raised exception: {e}. Trying fallback..."
            )

        # ── Secondary attempt ────────────────────────────────────────────────
        # Only attempt fallback if the key for that provider is available
        fallback_key_available = (
            (fallback_provider == "openai"      and bool(settings.OPENAI_API_KEY)) or
            (fallback_provider == "gemini"      and bool(settings.GEMINI_API_KEY)) or
            (fallback_provider == "groq"        and bool(settings.GROQ_API_KEY)) or
            (fallback_provider == "openrouter"  and bool(settings.OPENROUTER_API_KEY))
        )

        if fallback_key_available:
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
                last_error = result.get("error", "unknown")
                logger.warning(
                    f"[{caller}] Secondary provider ({fallback_provider}/{fallback_model}) "
                    f"returned error: {last_error}. Trying next tier..."
                )
            except Exception as e:
                last_error = str(e)
                logger.warning(
                    f"[{caller}] Secondary provider ({fallback_provider}/{fallback_model}) "
                    f"raised exception: {e}. Trying next tier..."
                )
        else:
            logger.warning(
                f"[{caller}] Secondary provider ({fallback_provider}) has no API key configured. Skipping."
            )



        # ── Groq final tier ──────────────────────────────────────────────────
        if bool(settings.GROQ_API_KEY) and "groq" not in tried:
            tried.add("groq")
            try:
                logger.info(f"[{caller}] Attempting Groq final tier: {settings.GROQ_MODEL}")
                result = await LLMService._dispatch(
                    provider="groq",
                    model=settings.GROQ_MODEL,
                    system_prompt=system_prompt,
                    user_prompt=user_prompt,
                    response_model=response_model,
                    temperature=temperature,
                    max_tokens=max_tokens,
                )
                if not (isinstance(result, dict) and "error" in result):
                    logger.info(f"[{caller}] Groq final tier succeeded.")
                    return result
                last_error = result.get("error", "unknown")
                logger.warning(f"[{caller}] Groq final tier returned error: {last_error}. Trying OpenRouter...")
            except Exception as e:
                last_error = str(e)
                logger.warning(f"[{caller}] Groq final tier failed: {e}. Trying OpenRouter...")

        # ── OpenRouter final tier ────────────────────────────────────────────
        if bool(settings.OPENROUTER_API_KEY) and "openrouter" not in tried:
            tried.add("openrouter")
            try:
                logger.info(f"[{caller}] Attempting OpenRouter final tier: meta-llama/llama-3.3-70b-instruct")
                result = await LLMService._dispatch(
                    provider="openrouter",
                    model="meta-llama/llama-3.3-70b-instruct",
                    system_prompt=system_prompt,
                    user_prompt=user_prompt,
                    response_model=response_model,
                    temperature=temperature,
                    max_tokens=max_tokens,
                )
                if not (isinstance(result, dict) and "error" in result):
                    logger.info(f"[{caller}] OpenRouter final tier succeeded.")
                    return result
                last_error = result.get("error", "unknown")
                logger.error(f"[{caller}] OpenRouter final tier returned error: {last_error}")
                return result
            except Exception as e:
                last_error = str(e)
                logger.error(f"[{caller}] OpenRouter final tier also failed: {e}")

        logger.error(
            f"[{caller}] All providers exhausted. Tried: {tried}. Last error: {last_error}"
        )
        return {"error": f"All providers failed. Last error: {last_error}", "raw": ""}

    @staticmethod
    def _clean_and_parse_json(content: str, provider: str = "") -> dict[str, Any] | str:
        """
        Robust parser for LLM structured output.

        Parsing order:
          Step 1 — Direct json.loads
          Step 2 — Strip markdown fences, retry json.loads
          Step 3 — Extract first {...} block, retry json.loads
          Step 4 — Strip <|python_tag|> prefix
          Step 5 — ast.literal_eval (handles Python dict literals)
          Step 6 — Graph completion detection: extract .text and re-parse
          Step 7 — Return raw text (never raises, never returns None)

        Returns a dict/list on success, or the raw str on total failure.
        NEVER returns None.
        NEVER raises an exception.
        """
        if not content:
            return ""

        tag = f"[{provider.upper() or 'LLM'}] Parser"

        # ── Helpers ──────────────────────────────────────────────────────────
        def try_json(text: str) -> dict[str, Any] | None:
            try:
                return json.loads(text)
            except (json.JSONDecodeError, ValueError):
                return None

        def try_python_literal(text: str) -> dict[str, Any] | list | None:
            import ast
            try:
                val = ast.literal_eval(text)
                if isinstance(val, (dict, list)):
                    return val
            except Exception:
                pass
            return None

        def strip_markdown(text: str) -> str:
            cleaned = text.strip()
            if cleaned.startswith("```"):
                lines = cleaned.split("\n")
                if lines[0].startswith("```"):
                    lines = lines[1:]
                if lines and lines[-1].strip() == "```":
                    lines = lines[:-1]
                return "\n".join(lines).strip()
            return cleaned

        def unwrap_graph_completion(parsed: dict | list | None) -> dict | list | str | None:
            """If parsed is a graph_completion wrapper, extract and return its .text field.
            Returns the original parsed object for all other dicts/lists.
            Returns None if parsed is None.
            """
            if isinstance(parsed, dict) and parsed.get("kind") == "graph_completion":
                inner_text = parsed.get("text", "")
                if inner_text:
                    inner_parsed = try_json(str(inner_text))
                    if inner_parsed is not None:
                        logger.info(f"{tag}: Unwrapped graph_completion.text as JSON")
                        return inner_parsed
                    logger.info(f"{tag}: Unwrapped graph_completion.text as raw string")
                    return str(inner_text)
            return parsed

        def extract_first_block(text: str) -> str | None:
            start_idx = text.find("{")
            end_idx = text.rfind("}")
            if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
                return text[start_idx : end_idx + 1]
            return None

        raw_content = content
        current = content.strip()

        # ── Step 1: Direct JSON parse ─────────────────────────────────────────
        res = try_json(current)
        if res is not None:
            logger.info(f"{tag}: Step 1 — JSON parser succeeded")
            return unwrap_graph_completion(res) or res

        # ── Step 2: Strip markdown fences, retry JSON ─────────────────────────
        cleaned_md = strip_markdown(current)
        if cleaned_md != current:
            res = try_json(cleaned_md)
            if res is not None:
                logger.info(f"{tag}: Step 2 — Markdown-stripped JSON parser succeeded")
                return unwrap_graph_completion(res) or res

        # ── Step 3: Extract first {...} block, retry JSON ─────────────────────
        extracted = extract_first_block(cleaned_md)
        if extracted:
            res = try_json(extracted)
            if res is not None:
                logger.info(f"{tag}: Step 3 — First-block JSON extraction succeeded")
                return unwrap_graph_completion(res) or res

        # ── Step 4: Strip <|python_tag|> prefix ──────────────────────────────
        if current.startswith("<|python_tag|>"):
            current = current[len("<|python_tag|>"):].strip()
            cleaned_md = strip_markdown(current)
            extracted = extract_first_block(cleaned_md)

        # ── Step 5: Python literal eval ───────────────────────────────────────
        for candidate in [cleaned_md, extracted, current]:
            if candidate:
                res = try_python_literal(candidate)
                if res is not None:
                    logger.info(f"{tag}: Step 5 — Python literal parser succeeded")
                    return unwrap_graph_completion(res) or res

        # ── Step 6: Graph completion via JSON (safety net) ────────────────────
        # If we reach here, Steps 1–5 all failed. Try a final JSON parse of any
        # remaining candidate and look for a graph_completion shape explicitly.
        for candidate in [cleaned_md, extracted, current]:
            if candidate:
                gc = try_json(candidate)
                if isinstance(gc, dict) and gc.get("kind") == "graph_completion":
                    inner_text = gc.get("text", "")
                    logger.info(f"{tag}: Step 6 — Graph completion (JSON) detected; extracting .text field")
                    if inner_text:
                        inner_parsed = try_json(str(inner_text))
                        if inner_parsed is not None:
                            logger.info(f"{tag}: Step 6 — graph_completion.text parsed as JSON")
                            return inner_parsed
                        logger.info(f"{tag}: Step 6 — Using graph_completion.text as raw text")
                        return str(inner_text)

        # ── Step 7: Return raw text — never fail ──────────────────────────────
        logger.info(f"{tag}: Step 7 — All structured parsers failed; returning raw text")
        return raw_content

    @staticmethod
    def _estimate_tokens(text: str) -> int:
        """Estimate token count for a given text using a standard character-based heuristic."""
        if not text:
            return 0
        # For code and structured JSON text, the token density is high: ~3 characters per token
        return max(1, int(len(text) / 3.0))

    @staticmethod
    def _trim_prompt_to_budget(system_prompt: str, user_prompt: str, limit_tokens: int) -> str:
        """
        Trims the context inside user_prompt to fit the specified token limit.
        Context memories are split by '\n\n---\n\n' and trimmed from the end.
        """
        marker = "=== END OF CONTEXT ==="
        if marker not in user_prompt:
            return user_prompt

        parts = user_prompt.split(marker, 1)
        context_part = parts[0]
        suffix = parts[1]

        prefix = "Repository Memory Context:\n\n"
        if not context_part.startswith(prefix):
            return user_prompt

        context_str = context_part[len(prefix):].strip()
        memories = [m.strip() for m in context_str.split("\n\n---\n\n") if m.strip()]

        sys_tokens = LLMService._estimate_tokens(system_prompt)
        suffix_tokens = LLMService._estimate_tokens(suffix)
        prefix_tokens = LLMService._estimate_tokens(prefix)
        non_context_tokens = sys_tokens + prefix_tokens + suffix_tokens

        if non_context_tokens >= limit_tokens:
            logger.warning("[Trimmer] Prompt base size without context already exceeds token limit!")
            return user_prompt

        budgeted_memories = []
        current_tokens = non_context_tokens

        for memory in memories:
            mem_tokens = LLMService._estimate_tokens(memory)
            if current_tokens + mem_tokens > limit_tokens:
                break
            budgeted_memories.append(memory)
            current_tokens += mem_tokens

        if len(budgeted_memories) < len(memories):
            trimmed_count = len(memories) - len(budgeted_memories)
            trimmed_chars = sum(len(m) for m in memories[len(budgeted_memories):])
            logger.warning(
                f"[Trimmer] Automatically trimmed {trimmed_count} memories "
                f"({trimmed_chars:,} chars, ~{current_tokens - non_context_tokens:,} tokens kept) "
                f"to stay within {limit_tokens:,} tokens limit."
            )

        new_context = "\n\n---\n\n".join(budgeted_memories)
        return f"{prefix}{new_context}\n\n{marker}{suffix}"

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
        # ── Trim if using Groq ────────────────────────────────────────────────
        if provider == "groq":
            limit_tokens = 8000
            if "llama-3.1-8b" in model:
                limit_tokens = 5800
            elif "llama-3.3-70b" in model:
                limit_tokens = 11800
            
            prompt_budget = limit_tokens - max_tokens
            if prompt_budget < 2000:
                prompt_budget = 2000
                
            user_prompt = LLMService._trim_prompt_to_budget(system_prompt, user_prompt, prompt_budget)

        # ── Strip the context boundary marker before sending to APIs ──────────
        user_prompt = user_prompt.replace("=== END OF CONTEXT ===", "").strip()

        # ── Instrumentation Log ──────────────────────────────────────────────
        sys_tokens = LLMService._estimate_tokens(system_prompt)
        user_tokens = LLMService._estimate_tokens(user_prompt)
        total_tokens = sys_tokens + user_tokens
        
        logger.info("=" * 80)
        logger.info(f"[LLM Dispatch] Provider: {provider} | Model: {model}")
        logger.info(f"[LLM Dispatch] System Prompt: {len(system_prompt):,} chars | ~{sys_tokens:,} tokens")
        logger.info(f"[LLM Dispatch] User Prompt:   {len(user_prompt):,} chars | ~{user_tokens:,} tokens")
        logger.info(f"[LLM Dispatch] Total Prompt:  {len(system_prompt)+len(user_prompt):,} chars | ~{total_tokens:,} tokens")
        logger.info(f"[LLM Dispatch] Max Output Tokens: {max_tokens}")
        logger.info("=" * 80)

        if provider == "openai":
            return await LLMService._generate_openai(
                system_prompt, user_prompt, response_model, temperature, max_tokens, model
            )
        elif provider == "gemini":
            return await LLMService._generate_gemini(
                system_prompt, user_prompt, response_model, temperature, max_tokens, model
            )

        elif provider == "groq":
            return await LLMService._generate_groq(
                system_prompt, user_prompt, response_model, temperature, max_tokens, model
            )
        elif provider == "openrouter":
            return await LLMService._generate_openrouter(
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
        from openai import AsyncOpenAI, RateLimitError, APIStatusError, APIConnectionError, APITimeoutError

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
                    # _clean_and_parse_json always returns str or dict — never None
                    parsed = LLMService._clean_and_parse_json(content, provider="openai")
                    return parsed

                return content or ""

            except RateLimitError as e:
                err_msg = str(e).lower()
                is_permanent = any(keyword in err_msg for keyword in ["tokens per day", "tpd", "daily quota", "daily token limit", "rate_limit_exceeded"])
                if is_permanent:
                    logger.error(f"OpenAI Daily Quota Exhausted: {e}")
                    return {"error": "OpenAI Daily Quota Exhausted", "raw": ""}

                if attempt < _OPENAI_MAX_RETRIES - 1:
                    wait = 10 * (attempt + 1)
                    logger.warning(f"OpenAI rate limit hit. Retrying in {wait}s... (attempt {attempt+1})")
                    await asyncio.sleep(wait)
                else:
                    logger.error(f"OpenAI rate limit — max retries reached: {e}")
                    return {"error": "OpenAI rate limit exceeded after retries", "raw": ""}

            except APIStatusError as e:
                is_transient = e.status_code >= 500 or e.status_code == 429
                if is_transient and attempt < _OPENAI_MAX_RETRIES - 1:
                    wait = 10 * (attempt + 1)
                    logger.warning(f"OpenAI 429/5xx error. Retrying in {wait}s...")
                    await asyncio.sleep(wait)
                else:
                    logger.error(f"OpenAI API error ({e.status_code}): {e}")
                    return {"error": f"OpenAI API error: {str(e)[:200]}", "raw": ""}

            except (APIConnectionError, APITimeoutError, asyncio.TimeoutError) as e:
                if attempt < _OPENAI_MAX_RETRIES - 1:
                    wait = 10 * (attempt + 1)
                    logger.warning(f"OpenAI connection/timeout error. Retrying in {wait}s... (attempt {attempt+1})")
                    await asyncio.sleep(wait)
                else:
                    logger.error(f"OpenAI connection/timeout error — max retries reached: {e}")
                    return {"error": "OpenAI connection/timeout exceeded after retries", "raw": ""}

        return {"error": "OpenAI: exhausted retries", "raw": ""}

    @staticmethod
    async def _generate_gemini(
        system_prompt: str,
        user_prompt: str,
        response_model: Type[BaseModel] | None,
        temperature: float,
        max_tokens: int,
        model: str = "gemini-2.5-flash",
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
                    # Use the shared robust parser — handles markdown fences, Python literals, etc.
                    parsed = LLMService._clean_and_parse_json(content, provider="gemini")
                    return parsed

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



    @staticmethod
    async def _generate_groq(
        system_prompt: str,
        user_prompt: str,
        response_model: Type[BaseModel] | None,
        temperature: float,
        max_tokens: int,
        model: str | None = None,
    ) -> dict[str, Any] | str:
        """Generate response using Groq API (OpenAI-compatible) with retry on rate limits."""
        from openai import AsyncOpenAI, RateLimitError, APIStatusError, APIConnectionError, APITimeoutError

        if not settings.GROQ_API_KEY:
            return {"error": "Groq API key not configured", "raw": ""}

        if not model:
            model = settings.GROQ_MODEL

        client = AsyncOpenAI(
            api_key=settings.GROQ_API_KEY,
            base_url="https://api.groq.com/openai/v1",
        )

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

        final_system_prompt = messages[0]["content"]
        final_user_prompt = messages[1]["content"]
        print("=" * 80)
        print(f"Groq Model: {model}")
        print(f"System Prompt Length: {len(final_system_prompt):,} chars")
        print(f"User Prompt Length: {len(final_user_prompt):,} chars")
        print(f"Total Prompt Length: {len(final_system_prompt) + len(final_user_prompt):,} chars")
        print(f"Max Output Tokens: {max_tokens}")
        print("=" * 80)

        for attempt in range(_GROQ_MAX_RETRIES):
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
                    # _clean_and_parse_json always returns str or dict — never None
                    parsed = LLMService._clean_and_parse_json(content, provider="groq")
                    return parsed

                return content or ""

            except RateLimitError as e:
                err_msg = str(e).lower()
                is_permanent = any(keyword in err_msg for keyword in ["tokens per day", "tpd", "daily quota", "daily token limit", "rate_limit_exceeded"])
                if is_permanent:
                    logger.warning("Groq Daily Quota Exhausted")
                    logger.warning("Skipping retries")
                    logger.warning("Switching to OpenRouter")
                    return {"error": "Groq Daily Quota Exhausted", "raw": ""}

                if attempt < _GROQ_MAX_RETRIES - 1:
                    wait = 10 * (attempt + 1)
                    logger.warning(f"Groq rate limit hit. Retrying in {wait}s... (attempt {attempt+1})")
                    await asyncio.sleep(wait)
                else:
                    logger.error(f"Groq rate limit — max retries reached: {e}")
                    return {"error": "Groq rate limit exceeded after retries", "raw": ""}

            except APIStatusError as e:
                is_transient = e.status_code >= 500 or e.status_code == 429
                if is_transient and attempt < _GROQ_MAX_RETRIES - 1:
                    wait = 10 * (attempt + 1)
                    logger.warning(f"Groq 429/5xx error. Retrying in {wait}s...")
                    await asyncio.sleep(wait)
                else:
                    logger.error(f"Groq API error ({e.status_code}): {e}")
                    return {"error": f"Groq API error: {str(e)[:200]}", "raw": ""}

            except (APIConnectionError, APITimeoutError, asyncio.TimeoutError) as e:
                if attempt < _GROQ_MAX_RETRIES - 1:
                    wait = 10 * (attempt + 1)
                    logger.warning(f"Groq connection/timeout error. Retrying in {wait}s... (attempt {attempt+1})")
                    await asyncio.sleep(wait)
                else:
                    logger.error(f"Groq connection/timeout error — max retries reached: {e}")
                    return {"error": "Groq connection/timeout exceeded after retries", "raw": ""}

        return {"error": "Groq: exhausted retries", "raw": ""}

    @staticmethod
    async def _generate_openrouter(
        system_prompt: str,
        user_prompt: str,
        response_model: Type[BaseModel] | None,
        temperature: float,
        max_tokens: int,
        model: str = "meta-llama/llama-3.3-70b-instruct",
    ) -> dict[str, Any] | str:
        """Generate response using OpenRouter API (OpenAI-compatible) with retry on rate limits."""
        from openai import AsyncOpenAI, RateLimitError, APIStatusError, APIConnectionError, APITimeoutError

        if not settings.OPENROUTER_API_KEY:
            return {"error": "OpenRouter API key not configured", "raw": ""}

        client = AsyncOpenAI(
            api_key=settings.OPENROUTER_API_KEY,
            base_url="https://openrouter.ai/api/v1",
        )

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

        for attempt in range(_OPENROUTER_MAX_RETRIES):
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
                    # _clean_and_parse_json always returns str or dict — never None
                    parsed = LLMService._clean_and_parse_json(content, provider="openrouter")
                    return parsed

                return content or ""

            except RateLimitError as e:
                err_msg = str(e).lower()
                is_permanent = any(keyword in err_msg for keyword in ["tokens per day", "tpd", "daily quota", "daily token limit", "rate_limit_exceeded"])
                if is_permanent:
                    logger.error(f"OpenRouter Daily Quota Exhausted: {e}")
                    return {"error": "OpenRouter Daily Quota Exhausted", "raw": ""}

                if attempt < _OPENROUTER_MAX_RETRIES - 1:
                    wait = 10 * (attempt + 1)
                    logger.warning(f"OpenRouter rate limit hit. Retrying in {wait}s... (attempt {attempt+1})")
                    await asyncio.sleep(wait)
                else:
                    logger.error(f"OpenRouter rate limit — max retries reached: {e}")
                    return {"error": "OpenRouter rate limit exceeded after retries", "raw": ""}

            except APIStatusError as e:
                is_transient = e.status_code >= 500 or e.status_code == 429
                if is_transient and attempt < _OPENROUTER_MAX_RETRIES - 1:
                    wait = 10 * (attempt + 1)
                    logger.warning(f"OpenRouter 429/5xx error. Retrying in {wait}s...")
                    await asyncio.sleep(wait)
                else:
                    logger.error(f"OpenRouter API error ({e.status_code}): {e}")
                    return {"error": f"OpenRouter API error: {str(e)[:200]}", "raw": ""}

            except (APIConnectionError, APITimeoutError, asyncio.TimeoutError) as e:
                if attempt < _OPENROUTER_MAX_RETRIES - 1:
                    wait = 10 * (attempt + 1)
                    logger.warning(f"OpenRouter connection/timeout error. Retrying in {wait}s... (attempt {attempt+1})")
                    await asyncio.sleep(wait)
                else:
                    logger.error(f"OpenRouter connection/timeout error — max retries reached: {e}")
                    return {"error": "OpenRouter connection/timeout exceeded after retries", "raw": ""}

        return {"error": "OpenRouter: exhausted retries", "raw": ""}
