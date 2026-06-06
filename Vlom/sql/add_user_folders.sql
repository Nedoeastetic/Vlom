-- Выполните этот файл один раз в Supabase SQL Editor.

create extension if not exists pgcrypto;

create table if not exists public.note_folders (
    id uuid primary key default gen_random_uuid(),
    userid uuid not null references auth.users(id) on delete cascade,
    name text not null check (char_length(trim(name)) between 1 and 80),
    created_at timestamptz not null default now(),
    unique (userid, name)
);

alter table public.notes
add column if not exists folder_id uuid null;

do $$
begin
    if not exists (
        select 1
        from pg_constraint
        where conname = 'notes_folder_id_fkey'
    ) then
        alter table public.notes
        add constraint notes_folder_id_fkey
        foreign key (folder_id)
        references public.note_folders(id)
        on delete set null;
    end if;
end $$;

create index if not exists note_folders_userid_idx
on public.note_folders(userid);

create index if not exists notes_userid_folder_id_idx
on public.notes(userid, folder_id);

alter table public.note_folders enable row level security;
alter table public.notes enable row level security;

drop policy if exists "folders_select_own" on public.note_folders;
create policy "folders_select_own"
on public.note_folders
for select
using (auth.uid() = userid);

drop policy if exists "folders_insert_own" on public.note_folders;
create policy "folders_insert_own"
on public.note_folders
for insert
with check (auth.uid() = userid);

drop policy if exists "folders_update_own" on public.note_folders;
create policy "folders_update_own"
on public.note_folders
for update
using (auth.uid() = userid)
with check (auth.uid() = userid);

drop policy if exists "folders_delete_own" on public.note_folders;
create policy "folders_delete_own"
on public.note_folders
for delete
using (auth.uid() = userid);

-- Политики notes. Если у вас уже есть рабочие политики, эти команды
-- безопасно заменят политики с указанными именами.
drop policy if exists "notes_select_own" on public.notes;
create policy "notes_select_own"
on public.notes
for select
using (auth.uid() = userid);

drop policy if exists "notes_insert_own" on public.notes;
create policy "notes_insert_own"
on public.notes
for insert
with check (
    auth.uid() = userid
    and (
        folder_id is null
        or exists (
            select 1
            from public.note_folders f
            where f.id = folder_id
              and f.userid = auth.uid()
        )
    )
);

drop policy if exists "notes_update_own" on public.notes;
create policy "notes_update_own"
on public.notes
for update
using (auth.uid() = userid)
with check (
    auth.uid() = userid
    and (
        folder_id is null
        or exists (
            select 1
            from public.note_folders f
            where f.id = folder_id
              and f.userid = auth.uid()
        )
    )
);

drop policy if exists "notes_delete_own" on public.notes;
create policy "notes_delete_own"
on public.notes
for delete
using (auth.uid() = userid);
