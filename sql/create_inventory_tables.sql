create extension if not exists pgcrypto;

create table if not exists inventory_items (
  id uuid primary key default gen_random_uuid(),
  warehouse_date text not null,
  folder_name text not null,
  product_name text,
  normalized_product_name text,
  source_file_stem text,
  brand text,
  model text,
  category text,
  condition_summary text,
  missing_parts text,
  cleaning_status text,
  repair_status text,
  suggested_price numeric,
  min_price numeric,
  suggested_platforms jsonb not null default '[]'::jsonb,
  confidence numeric not null default 0,
  needs_review boolean not null default false,
  source_type text not null default 'purchased_inventory',
  image_count int not null default 0,
  created_at timestamptz not null default now()
);

create table if not exists inventory_item_images (
  id uuid primary key default gen_random_uuid(),
  inventory_item_id uuid not null references inventory_items(id) on delete cascade,
  image_name text,
  image_url text,
  image_order int not null default 1,
  created_at timestamptz not null default now()
);

create table if not exists inventory_marketing_assets (
  id uuid primary key default gen_random_uuid(),
  inventory_item_id uuid not null references inventory_items(id) on delete cascade,
  listing_title text,
  short_description text,
  facebook_post text,
  threads_post text,
  hashtags jsonb not null default '[]'::jsonb,
  seo_keywords jsonb not null default '[]'::jsonb,
  created_at timestamptz not null default now()
);

create index if not exists inventory_items_created_at_idx on inventory_items (created_at desc);
create index if not exists inventory_items_warehouse_date_idx on inventory_items (warehouse_date desc);
create index if not exists inventory_items_needs_review_idx on inventory_items (needs_review);
create index if not exists inventory_item_images_item_id_idx on inventory_item_images (inventory_item_id);
create index if not exists inventory_marketing_assets_item_id_idx on inventory_marketing_assets (inventory_item_id);
