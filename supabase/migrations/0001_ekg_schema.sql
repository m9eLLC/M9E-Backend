-- Equipment Knowledge Graph (EKG) - pgvector-in-Supabase
-- M9E Technical Development Plan v1.0, Section 4.2

create extension if not exists vector;

-- Canonical equipment identity
create table if not exists ekg_entity (
  entity_id  text primary key,
  make       text not null,
  model      text not null,
  year       int,
  category   text not null,
  spec       jsonb not null default '{}',
  embedding  vector(1536),
  created_at timestamptz default now()
);

create index if not exists ekg_entity_embedding_idx
  on ekg_entity using ivfflat (embedding vector_cosine_ops);

-- Concrete instance for sale, resolved to an entity
create table if not exists ekg_listing (
  listing_id    text primary key,
  entity_id     text references ekg_entity(entity_id),
  hours         int,
  location      text,
  asking_price  numeric,
  raw           jsonb not null,
  status        text not null default 'active',
  created_at    timestamptz default now()
);

-- Similarity edge (the 'graph' relationship)
create table if not exists ekg_comparable (
  src_id     text not null,
  dst_id     text not null,
  similarity float not null,
  basis      jsonb not null, -- what drove the match
  primary key (src_id, dst_id)
);

-- Valuation lineage: evidence chain behind each price point
create table if not exists ekg_valuation (
  valuation_id  text primary key,
  listing_id    text references ekg_listing(listing_id),
  price_point   numeric not null,
  comparables   jsonb not null, -- ordered evidence set
  adjustments   jsonb not null,
  confidence    float not null,
  provenance    text not null,
  created_at    timestamptz default now()
);
