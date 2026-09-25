-- 福利厚生アプリ MVP スキーマ（Supabase / PostgreSQL）
-- スキーマ名: bts

create schema if not exists bts;

create table if not exists bts.tenants (
  id uuid primary key default gen_random_uuid(),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  name text not null,
  code text unique,
  active boolean not null default true,
  deleted_at timestamptz
);

create table if not exists bts.users (
  id uuid primary key default gen_random_uuid(),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  tenant_id uuid not null references bts.tenants(id),
  auth_id uuid unique,
  name text not null,
  role text not null default 'employee',
  department text,
  family text,
  interests text[],
  show_ranking boolean not null default false,
  last_search jsonb,
  deleted_at timestamptz
);

create table if not exists bts.areas (
  id uuid primary key default gen_random_uuid(),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  tenant_id uuid references bts.tenants(id),
  code text not null,
  name text not null,
  region text,
  sort int not null default 0
);
create unique index if not exists uq_areas_tenant_code on bts.areas (coalesce(tenant_id, '00000000-0000-0000-0000-000000000000'::uuid), code);

create table if not exists bts.menus (
  id uuid primary key default gen_random_uuid(),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  tenant_id uuid not null references bts.tenants(id),
  name text not null,
  category text not null,
  area_id uuid references bts.areas(id),
  address text,
  description text,
  photo_url text,
  map_url text,
  procedure text,
  usage_limit text,
  family_scope text,
  cancel_policy text,
  max_people int,
  visibility text not null default 'internal',
  hotel_ref text,
  matched boolean not null default false,
  content_updated_at date,
  deleted_at timestamptz
);

create table if not exists bts.plans (
  id uuid primary key default gen_random_uuid(),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  menu_id uuid not null references bts.menus(id),
  name text not null,
  room_type text,
  meal text,
  grade text,
  adults int,
  children int,
  nights int not null default 1,
  list_price int not null,
  benefit_price int not null,
  coupon_code text,
  coupon_price int,
  member_url text,
  child_pricing text,
  peak_note text,
  deleted_at timestamptz
);

create table if not exists bts.market_prices (
  id uuid primary key default gen_random_uuid(),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  menu_id uuid not null references bts.menus(id),
  hotel_ref text,
  checkin date not null,
  nights int not null,
  adults int not null,
  children int not null default 0,
  meal text,
  price int not null,
  source text not null,
  source_url text,
  fetched_at timestamptz not null,
  is_representative boolean not null default false
);

create table if not exists bts.posts (
  id uuid primary key default gen_random_uuid(),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  tenant_id uuid not null references bts.tenants(id),
  user_id uuid not null references bts.users(id),
  menu_id uuid not null references bts.menus(id),
  plan_id uuid references bts.plans(id),
  used_at date,
  rating int not null check (rating between 1 and 5),
  comment text,
  photo_url text,
  sentiment text,
  anonymous boolean not null default false,
  external_ok boolean not null default false,
  public_selected boolean not null default false,
  hidden boolean not null default false,
  view_count int not null default 0,
  deleted_at timestamptz
);

create table if not exists bts.activity_logs (
  id uuid primary key default gen_random_uuid(),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  tenant_id uuid not null references bts.tenants(id),
  user_id uuid not null references bts.users(id),
  menu_id uuid references bts.menus(id),
  plan_id uuid references bts.plans(id),
  kind text not null,
  occurred_at timestamptz not null default now()
);

create table if not exists bts.fetch_logs (
  id uuid primary key default gen_random_uuid(),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  tenant_id uuid not null references bts.tenants(id),
  started_at timestamptz not null,
  finished_at timestamptz,
  target_count int,
  success_count int not null default 0,
  fail_count int not null default 0,
  stopped boolean not null default false,
  note text
);

create table if not exists bts.spend (
  id uuid primary key default gen_random_uuid(),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  tenant_id uuid not null references bts.tenants(id),
  period_start date not null,
  period_end date not null,
  amount int not null,
  headcount int not null,
  unique (tenant_id, period_start, period_end)
);

create index if not exists idx_menus_tenant_area on bts.menus (tenant_id, area_id) where deleted_at is null;
create index if not exists idx_plans_menu on bts.plans (menu_id) where deleted_at is null;
create index if not exists idx_market_prices_menu_checkin on bts.market_prices (menu_id, checkin);
create index if not exists idx_posts_menu on bts.posts (menu_id) where deleted_at is null and hidden = false;
create index if not exists idx_activity_tenant_kind on bts.activity_logs (tenant_id, kind, occurred_at);

-- PostgRESTからbtsスキーマを読めるようにする（ダッシュボードの Exposed schemas にも bts を追加する）
grant usage on schema bts to anon, authenticated;
grant all on all tables in schema bts to anon, authenticated;
alter default privileges in schema bts grant all on tables to anon, authenticated;
