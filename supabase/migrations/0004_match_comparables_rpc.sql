-- Semantic + structured comparable retrieval for James 07 (Section 4.3).
-- Exposed as an RPC since pgvector's <=> distance operator isn't reachable
-- through PostgREST's plain filter syntax.

create or replace function match_comparables(
  query_embedding vector(1536),
  filter_category text,
  filter_year_lo int,
  filter_year_hi int,
  exclude_listing_id text,
  match_count int default 25
)
returns table (
  listing_id text,
  entity_id text,
  make text,
  model text,
  year int,
  asking_price numeric,
  hours int,
  similarity float
)
language sql stable
as $$
  select l.listing_id, e.entity_id, e.make, e.model, e.year, l.asking_price, l.hours,
         1 - (e.embedding <=> query_embedding) as similarity
  from ekg_listing l
  join ekg_entity e on e.entity_id = l.entity_id
  where e.category = filter_category
    and (filter_year_lo is null or e.year >= filter_year_lo)
    and (filter_year_hi is null or e.year <= filter_year_hi)
    and l.status = 'active'
    and l.listing_id != exclude_listing_id
  order by e.embedding <=> query_embedding
  limit match_count;
$$;

notify pgrst, 'reload schema';
