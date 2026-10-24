"""Proves retry + provider failover. No API keys needed."""
import pytest
from langchain_core.runnables import RunnableLambda

from app import config, llm


def boom(_):
    raise RuntimeError("provider down")


@pytest.fixture(autouse=True)
def fast_retries(monkeypatch):
    monkeypatch.setattr(config, "LLM_MAX_RETRIES", 1)  # no waiting in tests


def test_falls_back_when_primary_fails():
    chain = llm._with_resilience([RunnableLambda(boom), RunnableLambda(lambda x: "backup answer")])
    assert chain.invoke("hi") == "backup answer"


def test_tries_backups_in_order():
    chain = llm._with_resilience([
        RunnableLambda(boom), RunnableLambda(boom), RunnableLambda(lambda x: "third")])
    assert chain.invoke("hi") == "third"


def test_primary_used_when_healthy():
    chain = llm._with_resilience([RunnableLambda(lambda x: "primary"), RunnableLambda(boom)])
    assert chain.invoke("hi") == "primary"


def test_raises_when_every_model_fails():
    chain = llm._with_resilience([RunnableLambda(boom), RunnableLambda(boom)])
    with pytest.raises(RuntimeError):
        chain.invoke("hi")


def test_provider_chain_skips_backups_without_keys(monkeypatch):
    monkeypatch.setattr(config, "LLM_PROVIDER", "groq")
    monkeypatch.setattr(config, "LLM_MODEL", "m")
    monkeypatch.setattr(config, "LLM_FALLBACKS", ["gemini", "openai", "groq", "bogus"])
    monkeypatch.setenv("GOOGLE_API_KEY", "x")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    assert llm._provider_chain() == [("groq", "m"), ("gemini", "")]
