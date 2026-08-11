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
    """Placeholder envelope for agents not yet built (Mila 02, Inspection 03, Finance 04,
    Logistics 05, Intelligence 06): shape-correct per Section 3.3, but not backed by real
    invariant checks or the audit chain. Emma 01 and James 07 go through the real
    Truth Layer middleware instead - see app/truth/gate.py.
    """
    return TruthEnvelope(
        invariants_passed=ALL_INVARIANTS,
        invariants_failed=[],
        confidence=0.0,
        provenance=provenance,
        audit_ref=f"aud_stub_{uuid.uuid4().hex[:12]}",
    )
