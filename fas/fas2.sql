create database fas2 encoding = 'UTF8';
\c fas2

create trusted procedural language plpgsql
  handler plpgsql_call_handler
  validator plpgsql_validator;

CREATE SEQUENCE cert_seq;
SELECT setval('cert_seq', 1);

CREATE SEQUENCE person_seq;
-- TODO: Set this to start where our last person_id is
SELECT setval('person_seq', 1111);

CREATE SEQUENCE group_seq;
-- TODO: Set this to start where our last group_id is
SELECT setval('group_seq', 1222);

CREATE TABLE person (
    id INTEGER PRIMARY KEY NOT NULL DEFAULT nextval('person_seq'),
    username VARCHAR(32) UNIQUE NOT NULL,
    human_name TEXT NOT NULL,
    -- TODO: Switch to this?
    -- Also, app would be responsible for eliminating spaces and
    -- uppercasing
    -- gpg_fingerprint varchar(40),
    gpg_keyid VARCHAR(17),
    ssh_key TEXT,
    password VARCHAR(127) NOT NULL,
    comments TEXT,
    postal_address TEXT,
    telephone TEXT,
    facsimile TEXT,
    affiliation TEXT,
    certificate_serial INTEGER DEFAULT nextval('cert_seq'),
    creation TIMESTAMP DEFAULT NOW(),
    approval_status TEXT DEFAULT 'unapproved',
    internal_comments TEXT,
    ircnick TEXT,
    status TEXT,
    check ( status in ('active', 'vacation', 'inactive')),
    check ( gpg_keyid ~ '^[0-9A-F]{17}$')
);

CREATE TABLE configs (
    id SERIAL PRIMARY KEY,
    person_id integer references person(id),
    application text not null,
    attribute text not null,
    -- The value should be a simple value or a json string.
    -- Please create more config keys rather than abusing this with
    -- large datastructures.
    value text,
    check ( application in ('asterisk', 'moin', 'myfedora'))
);

CREATE TABLE groups (
    id INTEGER PRIMARY KEY NOT NULL DEFAULT nextval('group_seq'),
    name VARCHAR(32) UNIQUE NOT NULL,
    owner_id INTEGER NOT NULL REFERENCES person (id),
    group_type VARCHAR(16),
    needs_sponsor INTEGER DEFAULT 0,
    user_can_remove INTEGER DEFAULT 1,
    prerequisite_id INTEGER REFERENCES groups (id),
    joinmsg TEXT NULL DEFAULT '',
    check ( group_type in ('bugzilla','cvs', 'bzr', 'git', 'hg', 'mtn',
        'svn', 'shell', 'torrent', 'tracker', 'tracking', 'user') )
);

create table person_email (
    email text UNIQUE NOT NULL,
    group_id INTEGER references person(id) not null,
    purpose text not null,
    primary key (group_id, email),
    check ( purpose in ('bugzilla', 'primary', 'cla') ),
--    check ( email ~ "^[a-zA-Z0-9.]@[a-zA-Z0-9.]\.[a-zA-Z]$"),
    unique (group_id, purpose)
);

create table group_email (
    email text not null unique,
    group_id INTEGER references groups(id) not null,
    purpose text not null,
    primary key (group_id, email),
    check ( purpose in ('bugzilla', 'primary', 'cla') ),
    unique (group_id, purpose)
);

CREATE TABLE group_role (
    member_id INTEGER NOT NULL REFERENCES groups(id),
    group_id INTEGER NOT NULL REFERENCES groups(id),
    role_type text NOT NULL,
    role_status text DEFAULT 'unapproved',
    internal_comments text,
    sponsor_id INTEGER REFERENCES person(id),
    creation TIMESTAMP DEFAULT NOW(),
    approval TIMESTAMP DEFAULT NOW(),
    UNIQUE (member_id, group_id),
    check ( role_status in ('approved', 'unapproved') ),
    check ( role_type in ('user', 'administrator', 'sponsor') )
);

CREATE TABLE person_role (
    person_id INTEGER NOT NULL REFERENCES person (id),
    group_id INTEGER NOT NULL REFERENCES groups (id),
--  role_type is something like "user", "administrator", etc.
--  role_status tells us whether this has been approved or not
    role_type text NOT NULL,
    role_status text DEFAULT 'unapproved',
    internal_comments text,
    sponsor_id INTEGER REFERENCES person(id),
    creation TIMESTAMP DEFAULT NOW(),
    approval TIMESTAMP DEFAULT NOW(),
    UNIQUE (person_id, group_id),
    check ( role_status in ('approved', 'unapproved') ),
    check ( role_type in ('user', 'administrator', 'sponsor') )
);

-- action r == remove
-- action a == add
create table bugzilla_queue (
  email text not null,
  project_group_id int references groups(id) not null,
  person_id int references person(id) not null,
  action char(1) not null,
  primary key (email, project_group_id),
  check (action ~ '[ar]')
);

/*
create or replace function bugzilla_sync() returns trigger AS $bz_sync$
DECLARE
  newaction char(1);
  ROW role%ROWTYPE;
BEGIN
  if TG_OP = 'DELETE' then
    newaction:='r';
    ROW := OLD;
  else
    INSERT or UPDATE
    ROW := NEW;
    if NEW.role_status = 'approved' then
      newaction := 'a';
    else
      newaction := 'r';
    end if;
  end if;
  if ROW.project_group_id = id from project_group where name = 'fedorabugs' then
    if b.email is not Null from bugzilla_queue as b, person as p where p.id = ROW.person_id and b.email = p.email then
      update bugzilla_queue set action = newaction where email in (select email from person where id = ROW.person_id);
    else
      insert into bugzilla_queue select p.email, ROW.project_group_id, ROW.person_id, newaction from person as p where p.id = ROW.person_id;
    end if;
  end if;
  return ROW;
END;
$bz_sync$ language plpgsql;

create trigger role_bugzilla_sync before update or insert or delete
  on role
  for each row execute procedure bugzilla_sync();

create or replace function bugzilla_sync_email() returns trigger AS $bz_sync_e$
BEGIN
  if OLD.email = NEW.email then
    -- We only care if the email has been changed
    return NEW;
  end if;

  if p.id is not Null from person as p, role as r, project_group as g where p.id = OLD.id and g.name = 'fedorabugs' and r.role_status = 'approved' and r.project_group_id = g.id and r.person_id = p.id then
    -- Person belongs to the bugzilla changing group
    Remove old email
    if b.email is not Null from bugzilla_queue as b where b.email = OLD.email then
      update bugzilla_queue set action = 'r' where email = OLD.email;
    else
      insert into bugzilla_queue (select OLD.email, cast(g.id as int), OLD.id, 'r' from project_group as g where g.name = 'fedorabugs' limit 1);
    end if;
    Add new email
    if b.email is not Null from bugzilla_queue as b where b.email = NEW.email then
      update bugzilla_queue set action = 'a' where email = NEW.email;
    else
      insert into bugzilla_queue (select NEW.email, cast(g.id as int), NEW.id, 'a' from project_group as g where g.name = 'fedorabugs' limit 1);
    end if;
  end if;
  return NEW;
END;
$bz_sync_e$ language plpgsql;

create trigger email_bugzilla_sync before update
 on person
 for each row execute procedure bugzilla_sync_email();

*/

--GRANT ALL ON TABLE person, groups, person_role, group_role, cert_seq, person_seq, bugzilla_queue TO GROUP fedora;
