create schema if not exists content;

create table if not exists content.genre(
	id uuid primary key default gen_random_uuid(),
	name varchar(256) not null,
	description text,
	created timestamp with time zone not null default now(),
	modified timestamp with time zone default now(),
	Unique(name)
);

create table if not exists content.film_work(
	id uuid primary key default gen_random_uuid(),
	title varchar(256) not null,
	description text,
	creation_date date,
	rating float,
	type varchar(64) not null,
	created timestamp with time zone not null default now(),
	modified timestamp with time zone default now()
);

CREATE TABLE IF NOT EXISTS content.person (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    full_name VARCHAR(256) NOT NULL,
    created TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    modified TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

create table if not exists content.genre_film_work(
	id uuid primary key default gen_random_uuid(),
	genre_id uuid not null references content.genre(id) on delete cascade,
	film_work_id uuid not null references content.film_work(id) on delete cascade,
	created timestamp with time zone not null default now(),
	UNIQUE (genre_id, film_work_id)
);

CREATE TABLE IF NOT EXISTS content.person_film_work (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    person_id UUID NOT NULL REFERENCES content.person (id) ON DELETE CASCADE,
    film_work_id UUID NOT NULL REFERENCES content.film_work (id) ON DELETE CASCADE,
    role varchar(256) NOT NULL,
    created TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
	UNIQUE (person_id, film_work_id, role)
);

CREATE INDEX if not exists idx_film_work_creation_date ON content.film_work(creation_date DESC);
CREATE INDEX if not exists idx_film_work_rating ON content.film_work(rating DESC);
CREATE INDEX if not exists idx_film_work_title ON content.film_work(title);

CREATE INDEX if not exists idx_person_full_name ON content.person(full_name);

CREATE INDEX if not exists idx_genre_film_work on content.genre_film_work(film_work_id);

CREATE INDEX if not exists idx_person_film_work on content.person_film_work(film_work_id);