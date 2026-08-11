import hashlib
import json
import uuid
from datetime import datetime, timezone
from typing import List

from supabase import Client

GENESIS_HASH = "0" * 64


def _hash(data: dict) -> str:
    canonical = json.dumps(data, sort_keys=True, default=str)
    return hashlib.sha256(canonical.encode()).hexdigest()


def append(
    supabase: Client,
    agent_id: str,
    operation: str,
    input_data: dict,
    output_data: dict,
    invariants_passed: List[str],
    invariants_failed: List[str],
) -> str:
    """Appends a tamper-evident entry: each entry_hash covers its own content plus the
    previous entry's hash, so altering any past row breaks the chain from that point on.
    """
    last = (
        supabase.table("audit_chain")
        .select("entry_hash")
        .order("seq", desc=True)
        .limit(1)
        .execute()
    )
    prev_hash = last.data[0]["entry_hash"] if last.data else GENESIS_HASH

    entry_id = f"aud_{uuid.uuid4().hex[:16]}"
    created_at = datetime.now(timezone.utc).isoformat()

    entry_content = {
        "entry_id": entry_id,
        "agent_id": agent_id,
        "operation": operation,
        "input": input_data,
        "output": output_data,
        "invariants_passed": invariants_passed,
        "invariants_failed": invariants_failed,
        "prev_hash": prev_hash,
        "created_at": created_at,
    }
    entry_hash = _hash(entry_content)

    supabase.table("audit_chain").insert(
        {
            "entry_id": entry_id,
            "agent_id": agent_id,
            "operation": operation,
            "input": input_data,
            "output": output_data,
            "invariants_passed": invariants_passed,
            "invariants_failed": invariants_failed,
            "prev_hash": prev_hash,
            "entry_hash": entry_hash,
            "created_at": created_at,
        }
    ).execute()

    return entry_id
