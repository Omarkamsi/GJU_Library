-- Sky City Centre — Booking system schema
-- Run this in Supabase → SQL Editor → New query → Run

-- =========================================================
-- Table
-- =========================================================

create table if not exists public.appointments (
  id uuid primary key default gen_random_uuid(),
  name text not null,
  phone text not null,
  start_at timestamptz not null,
  duration_min int not null default 60,
  status text not null default 'booked' check (status in ('booked', 'cancelled')),
  created_by text not null default 'customer' check (created_by in ('customer', 'staff')),
  cancel_code text not null,
  notes text,
  created_at timestamptz not null default now()
);

create index if not exists idx_appointments_start_at on public.appointments(start_at);
create index if not exists idx_appointments_status on public.appointments(status);

-- One active (non-cancelled) booking per slot. Prevents double-booking at the DB level.
create unique index if not exists idx_appointments_unique_active_slot
  on public.appointments(start_at)
  where status = 'booked';

-- =========================================================
-- RLS — deny all direct table access; use functions instead
-- =========================================================

alter table public.appointments enable row level security;
-- No policies means anon cannot read/write the table directly.
-- Staff (edge function) uses service_role which bypasses RLS.

-- =========================================================
-- Public functions (callable by anyone via /rest/v1/rpc/*)
-- =========================================================

-- 1. Get booked slots in a date range — returns only start_at, no PII
create or replace function public.get_booked_slots(p_from timestamptz, p_to timestamptz)
returns table(start_at timestamptz)
language sql
security definer
set search_path = public
as $$
  select start_at from public.appointments
  where status = 'booked' and start_at >= p_from and start_at < p_to;
$$;

-- 2. Create a customer booking
create or replace function public.create_booking(
  p_name text,
  p_phone text,
  p_start_at timestamptz
)
returns table(id uuid, cancel_code text, start_at timestamptz)
language plpgsql
security definer
set search_path = public
as $$
declare
  v_id uuid;
  v_code text;
begin
  if p_name is null or length(trim(p_name)) = 0 then
    raise exception 'Name is required';
  end if;
  if p_phone is null or length(trim(p_phone)) = 0 then
    raise exception 'Phone is required';
  end if;
  if p_start_at <= now() then
    raise exception 'Cannot book in the past';
  end if;
  if p_start_at > now() + interval '60 days' then
    raise exception 'Too far in the future';
  end if;

  v_code := upper(substring(md5(random()::text || clock_timestamp()::text), 1, 6));

  insert into public.appointments (name, phone, start_at, cancel_code, created_by)
  values (trim(p_name), trim(p_phone), p_start_at, v_code, 'customer')
  returning appointments.id into v_id;

  return query select v_id as id, v_code as cancel_code, p_start_at as start_at;
end;
$$;

-- 3. Cancel a booking (requires id + cancel_code match)
create or replace function public.cancel_booking(p_id uuid, p_cancel_code text)
returns boolean
language plpgsql
security definer
set search_path = public
as $$
declare
  v_rows int;
begin
  update public.appointments
  set status = 'cancelled'
  where id = p_id
    and cancel_code = upper(p_cancel_code)
    and status = 'booked';
  get diagnostics v_rows = row_count;
  return v_rows > 0;
end;
$$;

-- 4. Lookup a booking by phone + cancel_code (for the manage page)
create or replace function public.lookup_booking(p_phone text, p_cancel_code text)
returns table(id uuid, name text, start_at timestamptz, status text)
language sql
security definer
set search_path = public
as $$
  select id, name, start_at, status
  from public.appointments
  where phone = p_phone and cancel_code = upper(p_cancel_code);
$$;

-- =========================================================
-- Grants — expose the four functions to the 'anon' role
-- =========================================================

grant execute on function public.get_booked_slots(timestamptz, timestamptz) to anon;
grant execute on function public.create_booking(text, text, timestamptz) to anon;
grant execute on function public.cancel_booking(uuid, text) to anon;
grant execute on function public.lookup_booking(text, text) to anon;
