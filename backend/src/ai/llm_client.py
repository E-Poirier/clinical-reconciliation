"""Thin wrapper around Anthropic Claude API for clinical reasoning.

Features:
- Retry with exponential backoff on RateLimitError and APITimeoutError
- In-memory cache keyed on hash(input_json)
- Timeout handling
"""

import hashlib
import json
import os
import time
from typing import Any

import anthropic
from anthropic import APITimeoutError, RateLimitError


# Default timeout in seconds
DEFAULT_TIMEOUT = 60.0
# Max retries for rate limit / timeout
MAX_RETRIES = 4
# Base delay for exponential backoff (seconds)
BASE_BACKOFF = 2.0


class LLMClient:
    """Wrapper for Anthropic Claude API with retry, cache, and timeout."""

    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
        timeout: float = DEFAULT_TIMEOUT,
        max_retries: int = MAX_RETRIES,
        cache_enabled: bool = True,
    ) -> None:
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        # Prefer env, then explicit arg; default to Sonnet 4 (widely available)
        self.model = model or os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-20250514")
        self.timeout = timeout
        self.max_retries = max_retries
        self.cache_enabled = cache_enabled
        self._cache: dict[str, str] = {}
        self._client: anthropic.Anthropic | None = None

    @property
    def client(self) -> anthropic.Anthropic:
        """Lazy-initialize Anthropic client."""
        if self._client is None:
            if not self.api_key:
                raise ValueError("ANTHROPIC_API_KEY is required for LLM calls")
            self._client = anthropic.Anthropic(
                api_key=self.api_key,
                timeout=anthropic.Timeout(self.timeout),
            )
        return self._client

    def _cache_key(self, system_prompt: str, user_prompt: str) -> str:
        """Generate cache key from prompt content."""
        content = json.dumps(
            {"system": system_prompt, "user": user_prompt},
            sort_keys=True,
            default=str,
        )
        return hashlib.sha256(content.encode()).hexdigest()

    def complete(
        self,
        system_prompt: str,
        user_prompt: str,
        max_tokens: int = 2048,
    ) -> str:
        """Call Claude API with retry, cache, and timeout.

        Args:
            system_prompt: System message (clinical context, instructions)
            user_prompt: User message (patient data, question)
            max_tokens: Maximum tokens in response

        Returns:
            Raw text content from the assistant message.

        Raises:
            ValueError: If API key is missing
            anthropic.APIError: On non-retryable API errors
        """
        if self.cache_enabled:
            key = self._cache_key(system_prompt, user_prompt)
            if key in self._cache:
                return self._cache[key]

        last_error: Exception | None = None
        for attempt in range(self.max_retries):
            try:
                response = self.client.messages.create(
                    model=self.model,
                    max_tokens=max_tokens,
                    system=system_prompt,
                    messages=[{"role": "user", "content": user_prompt}],
                )
                text = response.content[0].text
                if self.cache_enabled:
                    self._cache[key] = text
                return text
            except (RateLimitError, APITimeoutError) as e:
                last_error = e
                if attempt < self.max_retries - 1:
                    delay = BASE_BACKOFF * (2**attempt)
                    time.sleep(delay)
                else:
                    raise
            except anthropic.APIError as e:
                raise

        if last_error:
            raise last_error
        raise RuntimeError("Unexpected retry loop exit")
