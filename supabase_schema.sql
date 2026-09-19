-- Endesha hii kwenye Supabase SQL Editor mara moja tu, mwanzoni.
--
-- HATUNA table ya "users" hapa kwa makusudi: watumiaji wote (owner, client,
-- admin) wanahifadhiwa na Supabase Auth mwenyewe kwenye auth.users.
-- Jina, namba ya simu, na role (owner/client/admin) vinahifadhiwa kwenye
-- user_metadata ya kila mtumiaji (tazama routes/auth_routes.py na
-- create_admin.py), si kwenye jedwali letu.

create extension if not exists "pgcrypto";

-- Vyumba vilivyowekwa na wamiliki
create table if not exists rooms (
    id uuid primary key default gen_random_uuid(),
    owner_id uuid references auth.users(id) on delete cascade,
    title text not null,
    area text not null,                 -- eneo (mfano: Pasua, Majengo)
    distance_to_college numeric,        -- umbali kwa km kutoka chumba hadi chuo
    price numeric not null,
    room_type text not null,            -- mfano: single, shared, self-contained
    features text,                      -- sifa za chumba (umeme, maji, choo ndani, n.k)
    extra_directions text,              -- maelekezo ya ziada ya kufika
    contact_phone text not null,
    status text not null default 'available'
        check (status in ('available', 'requested', 'pending_payment', 'booked', 'archived')),
    created_at timestamptz default now()
);

-- Picha/video za kila chumba (Cloudinary URLs)
create table if not exists room_media (
    id uuid primary key default gen_random_uuid(),
    room_id uuid references rooms(id) on delete cascade,
    url text not null,
    media_type text not null check (media_type in ('image', 'video')),
    public_id text not null,            -- Cloudinary public_id, kwa ajili ya kufuta baadaye
    created_at timestamptz default now()
);

-- Maombi: yanaweza kuwa request ya chumba fulani, au custom request (chumba hakipo)
create table if not exists requests (
    id uuid primary key default gen_random_uuid(),
    request_type text not null check (request_type in ('room_request', 'custom_request')),
    room_id uuid references rooms(id) on delete set null,
    client_id uuid references auth.users(id) on delete cascade,
    owner_id uuid references auth.users(id) on delete set null,
    desired_area text,
    desired_distance numeric,
    desired_room_type text,
    desired_price numeric,
    notes text,
    status text not null default 'pending'
        check (status in ('pending', 'connected', 'payment_in_progress', 'booked', 'cancelled')),
    admin_notes text,
    created_at timestamptz default now()
);

create index if not exists idx_rooms_status on rooms(status);
create index if not exists idx_requests_status on requests(status);
