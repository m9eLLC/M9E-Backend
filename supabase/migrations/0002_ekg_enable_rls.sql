-- Lock the EKG tables down to the backend's service_role key only.
-- Per Section 2 of the TDP: "The marketplace UI never speaks to agents directly;
-- it calls clean gateway endpoints." There is no legitimate direct client (anon/
-- authenticated) access path to the EKG - all reads/writes go through the FastAPI
-- gateway, which connects with the service_role key and therefore bypasses RLS
-- regardless of policies defined here. Enabling RLS with zero policies for
-- anon/authenticated is intentional: it denies all direct client access by default.

alter table public.ekg_entity enable row level security;
alter table public.ekg_listing enable row level security;
alter table public.ekg_comparable enable row level security;
alter table public.ekg_valuation enable row level security;
