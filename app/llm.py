"""Builds the chat model with retries and provider failover.

Order of attempts: primary model (retried) -> each fallback provider (retried).
Fallback providers are listed in LLM_FALLBACKS and are skipped if their API key is missing.
"""
import os
from functools import lru_cache

from app import config


def _build(provider: str, model: str = ""):
    model = model or config.DEFAULT_MODELS[provider]
    if provider == "groq":
        from langchain_groq import ChatGroq
        return ChatGroq(model=model, temperature=0)
    if provider == "gemini":
        from langchain_google_genai import ChatGoogleGenerativeAI
        return ChatGoogleGenerativeAI(model=model, temperature=0)
    if provider == "nvidia":
        try:
            from langchain_nvidia_ai_endpoints import ChatNVIDIA
        except ImportError:
            from langchain_nvidia_ai_endpoints.chat_models import ChatNVIDIA
        return ChatNVIDIA(model=model, temperature=0)
    raise ValueError(f"Unknown provider '{provider}'. Use groq, gemini or nvidia.")


def _provider_chain() -> list[tuple[str, str]]:
    """[(provider, model), ...] with the primary first, then usable fallbacks."""
    chain = [(config.LLM_PROVIDER, config.LLM_MODEL)]
    for provider in config.LLM_FALLBACKS:
        if provider in {p for p, _ in chain} or provider not in config.API_KEY_ENV:
            continue
        if not os.getenv(config.API_KEY_ENV[provider]):
            continue  # no key for this backup, so it could never work
        chain.append((provider, ""))
    return chain


def _with_resilience(runnables: list):
    """Wrap each runnable with retries, then chain them as fallbacks."""
    wrapped = [r.with_retry(stop_after_attempt=config.LLM_MAX_RETRIES) for r in runnables]
    primary, backups = wrapped[0], wrapped[1:]
    return primary.with_fallbacks(backups) if backups else primary


@lru_cache(maxsize=1)
def get_llm():
    """Plain text model (used for drafting)."""
    return _with_resilience([_build(p, m) for p, m in _provider_chain()])


@lru_cache(maxsize=8)
def get_structured_llm(schema):
    """Model that returns a validated Pydantic object.

    Structured output is applied to each model BEFORE chaining fallbacks, so every
    backup also returns the same schema.
    """
    return _with_resilience([_build(p, m).with_structured_output(schema)
                             for p, m in _provider_chain()])
