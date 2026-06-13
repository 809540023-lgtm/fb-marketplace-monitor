create extension if not exists pgcrypto;

create table if not exists product_logs (
  id uuid primary key default gen_random_uuid(),
  run_id text not null,
  stage text not null,
  status text not null default 'completed',
  query text,
  payload jsonb not null,
  created_at timestamptz not null default now()
);

create index if not exists product_logs_run_id_idx on product_logs (run_id);
create index if not exists product_logs_stage_idx on product_logs (stage);
create index if not exists product_logs_created_at_idx on product_logs (created_at desc);
