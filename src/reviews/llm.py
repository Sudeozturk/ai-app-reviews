import hashlib
import os
import re
import time
from dataclasses import dataclass

from google import genai
from google.genai import errors as genai_errors
from google.genai import types

from reviews.db import get_connection

DEFAULT_MODEL = os.environ.get("GEMINI_MODEL", "gemini-3.6-flash")

LOG_SQL = """
INSERT INTO llm_calls (
    model, prompt_sha, prompt_tokens, output_tokens,
    total_tokens, duration_ms, ok, error
)
VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
"""


@dataclass(frozen=True)
class LLMResponse:
    text: str
    model: str
    prompt_tokens: int | None
    output_tokens: int | None
    total_tokens: int | None
    duration_ms: int


def _sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


def _log_call(
    model: str,
    prompt_sha: str,
    prompt_tokens: int | None,
    output_tokens: int | None,
    total_tokens: int | None,
    duration_ms: int,
    ok: bool,
    error: str | None,
) -> None:
    try:
        with get_connection() as conn:
            conn.execute(
                LOG_SQL,
                (
                    model,
                    prompt_sha,
                    prompt_tokens,
                    output_tokens,
                    total_tokens,
                    duration_ms,
                    ok,
                    error,
                ),
            )
    except Exception:
        pass


def _complete_once(prompt: str, model: str | None = None) -> LLMResponse:
    model = model or DEFAULT_MODEL
    prompt_sha = _sha(prompt)
    client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
    started = time.monotonic()

    try:
        raw = client.models.generate_content(
            model=model,
            contents=prompt,
            config=types.GenerateContentConfig(
                thinking_config=types.ThinkingConfig(thinking_budget=0),
                temperature=0,
                response_mime_type="application/json",
            ),
        )
    except Exception as exc:
        duration_ms = int((time.monotonic() - started) * 1000)
        _log_call(model, prompt_sha, None, None, None, duration_ms, False, str(exc)[:500])
        raise

    duration_ms = int((time.monotonic() - started) * 1000)
    usage = raw.usage_metadata
    response = LLMResponse(
        text=raw.text or "",
        model=model,
        prompt_tokens=usage.prompt_token_count,
        output_tokens=usage.candidates_token_count,
        total_tokens=usage.total_token_count,
        duration_ms=duration_ms,
    )
    _log_call(
        model,
        prompt_sha,
        response.prompt_tokens,
        response.output_tokens,
        response.total_tokens,
        duration_ms,
        True,
        None,
    )
    return response


class DailyQuotaExceeded(RuntimeError):
    pass


RETRYABLE_CODES = {429, 500, 503}


def complete(prompt: str, model: str | None = None, max_attempts: int = 4) -> LLMResponse:
    delay = 2.0
    for attempt in range(1, max_attempts + 1):
        try:
            return _complete_once(prompt, model)
        except genai_errors.APIError as exc:
            code = getattr(exc, "code", None)
            message = str(exc)
            if code == 429 and "PerDay" in message:
                raise DailyQuotaExceeded(message[:200]) from exc
            if code not in RETRYABLE_CODES or attempt == max_attempts:
                raise
            match = re.search(r"'retryDelay': '(\d+)s'", message)
            wait = float(match.group(1)) + 1 if match else delay
            time.sleep(wait)
            delay *= 2
    raise RuntimeError("buraya ulaşılmamalı")
