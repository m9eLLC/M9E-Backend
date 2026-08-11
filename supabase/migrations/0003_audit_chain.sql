-- Cryptographic audit chain (Section 2 architecture, T-M6 Auditability).
-- Each entry hashes its own content plus the previous entry's hash, so any
-- tampering with an existing row breaks the chain for everything after it.

create table if not exists audit_chain (
  seq                bigserial primary key,
  entry_id           text unique not null,
  agent_id           text not null,
  operation          text not null,
  input              jsonb not null,
  output             jsonb not null,
  invariants_passed  jsonb not null,
  invariants_failed  jsonb not null,
  prev_hash          text not null,
  entry_hash         text not null,
  created_at         timestamptz not null default now()
);

create index if not exists audit_chain_agent_id_idx on audit_chain (agent_id);

-- Backend-only, same rationale as the EKG tables: no direct client access.
alter table audit_chain enable row level security;
