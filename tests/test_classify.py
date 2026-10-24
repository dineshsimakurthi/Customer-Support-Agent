"""Measures classifier accuracy against labelled tickets. Needs a real LLM key.

Run:  pytest tests/test_classify.py -s
"""
import json
import os

import pytest

from app import config

pytestmark = pytest.mark.skipif(
    not os.getenv(config.API_KEY_ENV.get(config.LLM_PROVIDER, "")),
    reason="No LLM API key set; skipping live classification test",
)


def load_cases():
    cases = json.loads((config.TESTS_DIR / "test_set.json").read_text())
    holdout = config.TESTS_DIR / "bitext_holdout.json"  # created by ingest_kb.py
    if holdout.exists():
        cases += json.loads(holdout.read_text())
    return cases


def test_category_accuracy():
    from app.nodes.classify import run_classifier

    cases = load_cases()
    correct, wrong = 0, []
    for case in cases:
        pred = run_classifier(case["ticket"]).category
        if pred == case["category"]:
            correct += 1
        else:
            wrong.append((case["ticket"][:60], case["category"], pred))
    accuracy = correct / len(cases)
    print(f"\nCategory accuracy: {accuracy:.0%} ({correct}/{len(cases)})")
    for w in wrong:
        print("  MISS:", w)
    assert accuracy >= 0.70


def test_angry_tickets_detected():
    from app.nodes.classify import run_classifier

    angry = [c for c in load_cases() if c.get("sentiment") == "angry"]
    for case in angry:
        assert run_classifier(case["ticket"]).sentiment == "angry", case["ticket"]
