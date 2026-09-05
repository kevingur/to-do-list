-- Supabase > SQL Editor'a yapıştırıp Run de.

create table if not exists todos (
  id           uuid primary key default gen_random_uuid(),
  name         text not null,
  description  text default '',
  due          date not null,
  done         boolean not null default false,
  created_at   timestamptz not null default now(),
  completed_at timestamptz
);

create table if not exists todo_log (
  id         bigserial primary key,
  ts         timestamptz not null default now(),
  action     text not null,
  todo_id    uuid,
  todo_name  text
);

-- RLS açık kalsın: tarayıcıdan/anon anahtarla kimse veriye ulaşamaz.
-- Uygulama sunucu tarafında service_role anahtarıyla bağlanır ve RLS'i geçer.
alter table todos    enable row level security;
alter table todo_log enable row level security;
