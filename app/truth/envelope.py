import uuid

from pydantic import BaseModel

ALL_INVARIANTS = ["T-M1", "T-M2", "T-M3", "T-M4", "T-M5", "T-M6"]


class TruthEnvelope(BaseModel):
    invariants_passed: list[str]
    invariants_failed: list[str]
    confidence: float
    provenance: str
    audit_ref: str


def stub_envelope(provenance: str) -> TruthEnvelope:
    """Session 1 placeholder envelope: shape-correct per Section 3.3, but not yet backed
    by real invariant checks or the audit chain. Those land with the Session 3 Truth Layer
    middleware (Section 5) - see app/truth/gate.py.
    """
    return TruthEnvelope(
        invariants_passed=ALL_INVARIANTS,
        invariants_failed=[],
        confidence=0.0,
        provenance=provenance,
        audit_ref=f"aud_stub_{uuid.uuid4().hex[:12]}",
    )


def envelope_with_confidence(provenance: str, confidence: float) -> TruthEnvelope:
    """Session 2: carries a real, agent-reported confidence and provenance chain, but
    invariants_passed/audit_ref are still placeholders - T-M1..T-M6 aren't actually
    checked and nothing is written to a cryptographic audit chain yet. That's Session 3.
    """
    return TruthEnvelope(
        invariants_passed=ALL_INVARIANTS,
        invariants_failed=[],
        confidence=confidence,
        provenance=provenance,
        audit_ref=f"aud_stub_{uuid.uuid4().hex[:12]}",
    )
