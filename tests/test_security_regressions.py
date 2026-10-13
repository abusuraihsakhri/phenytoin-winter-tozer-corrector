"""Audit signature tampering and mock-adapter disclosure regressions."""
from agents.base import AuditTrail
from agents.llm_factory import LLMFactory
import pytest


def test_audit_verifies_signature_not_only_chain():
    trail = AuditTrail(secret_key="unit-test-strong-hmac-key")
    trail.log("test", "test", "TEST", {"case": "demo"})
    assert trail.verify_integrity()
    snapshot = trail.get_trail()
    snapshot[0]["actor"] = "modified-copy"
    assert trail.verify_integrity()
    trail.logs[0]["actor"] = "forged"
    assert not trail.verify_integrity()


def test_mock_never_claims_external_verification():
    reply = LLMFactory.create("mock").invoke("Phenytoin equation")
    assert "No model inference or clinical verification" in reply
    with pytest.raises(ValueError):
        LLMFactory.create("openai")
