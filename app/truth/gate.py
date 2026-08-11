from typing import List

from supabase import Client

from app.truth import audit_chain
from app.truth.envelope import TruthEnvelope
from app.truth.invariants import run_invariants


class TruthViolation(Exception):
    def __init__(self, failed: List[str], audit_ref: str):
        self.failed = failed
        self.audit_ref = audit_ref
        super().__init__(f"Truth invariants failed: {failed} (audit_ref={audit_ref})")


def truth_gate(supabase: Client, agent_id: str, op: str, input_data: dict, result: dict) -> TruthEnvelope:
    """Mandatory validation every agent output passes through (Section 5).

    Checks T-M1..T-M6 against the result, appends a tamper-evident entry to the audit
    chain, and raises TruthViolation if any invariant failed - the gateway then rejects
    the output instead of releasing it (Section 3.3). The audit append always happens
    before this returns or raises, which is what satisfies T-M6 for both outcomes.
    """
    checks = run_invariants(agent_id, op, result, supabase)
    audit_ref = audit_chain.append(
        supabase, agent_id, op, input_data, result, checks.passed, checks.failed
    )

    if checks.failed:
        raise TruthViolation(checks.failed, audit_ref)

    return TruthEnvelope(
        invariants_passed=checks.passed,
        invariants_failed=checks.failed,
        confidence=float(result.get("confidence", 0.0)),
        provenance=result.get("provenance", f"{agent_id}/{op}"),
        audit_ref=audit_ref,
    )
