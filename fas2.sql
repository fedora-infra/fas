-- Copyright © 2008  Red Hat, Inc. All rights reserved.
--
-- This copyrighted material is made available to anyone wishing to use, modify,
-- copy, or redistribute it subject to the terms and conditions of the GNU
-- General Public License v.2.  This program is distributed in the hope that it
-- will be useful, but WITHOUT ANY WARRANTY expressed or implied, including the
-- implied warranties of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
-- See the GNU General Public License for more details.  You should have
-- received a copy of the GNU General Public License along with this program;
-- if not, write to the Free Software Foundation, Inc., 51 Franklin Street,
-- Fifth Floor, Boston, MA 02110-1301, USA. Any Red Hat trademarks that are
-- incorporated in the source code or documentation are not subject to the GNU
-- General Public License and may only be used or replicated with the express
-- permission of Red Hat, Inc.
--
-- Author(s): Toshio Kuratomi <tkuratom@redhat.com>
--            Ricky Zhou <ricky@fedoraproject.org>
--            Mike McGrath <mmcgrath@redhat.com>
--
create database fas2 encoding = 'UTF8';
\c fas2

create procedural language plpythonu
  handler plpythonu_call_handler
  validator plpythonu_validator;

CREATE SEQUENCE person_seq;
-- TODO: Set this to start where our last person_id is
SELECT setval('person_seq', 1111);

CREATE TABLE people (
    -- tg_user::user_id
    id INTEGER PRIMARY KEY NOT NULL DEFAULT nextval('person_seq'),
    -- tg_user::user_name
    username VARCHAR(32) UNIQUE NOT NULL,
    -- tg_user::display_name
    human_name TEXT NOT NULL,
    -- TODO: Switch to this?
    -- Also, app would be responsible for eliminating spaces and
    -- uppercasing
    -- gpg_fingerprint varchar(40),
    gpg_keyid VARCHAR(64),
    ssh_key TEXT,
    -- tg_user::password
    password VARCHAR(127) NOT NULL,
    old_password VARCHAR(127),
    passwordtoken text null,
    password_changed TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    email TEXT not null unique,
    emailtoken TEXT,
    unverified_email TEXT,
    comments TEXT,
    postal_address TEXT,
    country_code char(2),
    telephone TEXT,
    facsimile TEXT,
    affiliation TEXT,
    certificate_serial INTEGER DEFAULT 1,
    -- tg_user::created
    creation TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    --approval_status TEXT DEFAULT 'unapproved',
    internal_comments TEXT,
    ircnick TEXT,
    last_seen TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    status TEXT DEFAULT 'active',
    status_change TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    locale TEXT not null DEFAULT 'C',
    timezone TEXT null DEFAULT 'UTC',
    latitude numeric,
    longitude numeric,
    privacy BOOLEAN DEFAULT FALSE,
    check (status in ('active', 'inactive', 'expired', 'admin_disabled'))
    --check (gpg_keyid ~ '^[0-9A-F]{17}$')
);

create index people_status_idx on people(status);
cluster people_status_idx on people;

CREATE TABLE configs (
    id SERIAL PRIMARY KEY,
    person_id integer references people(id) not null,
    application TEXT not null,
    attribute TEXT not null,
    -- The value should be a simple value or a json string.
    -- Please create more config keys rather than abusing this with
    -- large datastructures.
    value TEXT,
    check (application in ('asterisk', 'moin', 'myfedora' ,'openid', 'yubikey', 'bugzilla')),
    -- Might end up removing openid, depending on how far we take the provider
    unique (person_id, application, attribute)
);

create index configs_person_id_idx on configs(person_id);
create index configs_application_idx on configs(application);
cluster configs_person_id_idx on configs;

CREATE TABLE groups (
    -- tg_group::group_id
    id INTEGER PRIMARY KEY NOT NULL DEFAULT nextval('person_seq'),
    -- tg_group::group_name
    name VARCHAR(32) UNIQUE NOT NULL,
    -- tg_group::display_name
    display_name TEXT,
    url TEXT,
    mailing_list TEXT,
    mailing_list_url TEXT,
    irc_channel TEXT,
    irc_network TEXT,
    owner_id INTEGER NOT NULL REFERENCES people(id),
    group_type VARCHAR(16),
    needs_sponsor BOOLEAN DEFAULT FALSE,
    user_can_remove BOOLEAN DEFAULT TRUE,
    invite_only BOOLEAN DEFAULT FALSE,
    prerequisite_id INTEGER REFERENCES groups(id),
    joinmsg TEXT NULL DEFAULT '',
    apply_rules TEXT,
    -- tg_group::created
    creation TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    check (group_type in ('cla', 'system', 'bugzilla','cvs', 'bzr', 'git', 'hg', 'mtn',
        'svn', 'shell', 'torrent', 'tracker', 'tracking', 'user')) 
);

create index groups_group_type_idx on groups(group_type);
cluster groups_group_type_idx on groups;

CREATE TABLE person_roles (
    person_id INTEGER NOT NULL REFERENCES people(id),
    group_id INTEGER NOT NULL REFERENCES groups(id),
    --  role_type is something like "user", "administrator", etc.
    --  role_status tells us whether this has been approved or not
    role_type text NOT NULL,
    role_status text DEFAULT 'unapproved',
    internal_comments text,
    sponsor_id INTEGER REFERENCES people(id),
    creation TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    approval TIMESTAMP WITH TIME ZONE DEFAULT NULL,
    primary key (person_id, group_id),
    check (role_status in ('approved', 'unapproved')),
    check (role_type in ('user', 'administrator', 'sponsor'))
);

create index person_roles_person_id_idx on person_roles(person_id);
create index person_roles_group_id_idx on person_roles(group_id);
-- We could cluster on either person or group.  The choice of group is because
-- groups are larger and therefore will take more memory if guessed wrong.
-- Open to reevaluation.
cluster person_roles_group_id_idx on person_roles;

-- View for mod_auth_pgsql
create view user_group as select username, name as groupname from people as p, groups as g, person_roles as r where r.person_id=p.id and r.group_id=g.id and r.role_status='approved'; 

-- action r == remove
-- action a == add
create table bugzilla_queue (
    email text not null,
    group_id INTEGER references groups(id) not null,
    person_id INTEGER references people(id) not null,
    action CHAR(1) not null,
    primary key (email, group_id),
    check (action ~ '[ar]')
);

-- Log changes to the account system
create table log (
    id serial primary key,
    author_id INTEGER references people(id) not null,
    changetime TIMESTAMP WITH TIME ZONE default NOW(),
    description TEXT
);

create index log_changetime_idx on log(changetime);
cluster log_changetime_idx on log;

--
-- This table allows certain services to be restricted by hostname/ip/person.
--
-- Any time a request for a restricted action is requested, the FAS server
-- consults this table to see if the user@(hostname/ip) is allowed to access
-- the resource.  If approved is true, the request is granted.  If false or
-- null, the request is denied.
--
-- New records are created when a request is first made by a specific
-- username@(hostname/id)
--
create table requests (
    id serial primary key,
    person_id INTEGER not null references people(id),
    hostname TEXT not null,
    ip TEXT not null,
    action TEXT not null default 'trust_all',
    last_request TIMESTAMP WITH TIME ZONE default now() not null,
    approved boolean,
    unique (person_id, hostname, ip, action)
);

create index requests_last_request_idx on requests(last_request);
create index hostname_idx on requests(hostname);
create index ip_idx on requests(ip);
create index person_id_idx on requests(person_id);
cluster requests_last_request_idx on requests;

--
-- turbogears session tables
--
create table visit (
    visit_key CHAR(40) primary key,
    created TIMESTAMP WITH TIME ZONE not null default now(),
    expiry TIMESTAMP WITH TIME ZONE
);

create index visit_expiry_idx on visit(expiry);
cluster visit_expiry_idx on visit;

create table visit_identity (
    visit_key CHAR(40) primary key references visit(visit_key),
    user_id INTEGER references people(id),
    -- True if the user was authenticated using SSL
    ssl boolean
);

create table session (
  id varchar(40) primary key,
  data text,
  expiration_time timestamp
);

--
-- When the fedorabugs role is updated for a person, add them to bugzilla queue.
--
create or replace function bugzilla_sync() returns trigger as $bz_sync$
    # Decide which row we are operating on and the action to take
    if TD['event'] == 'DELETE':
        # 'r' for removing an entry from bugzilla
        newaction = 'r'
        row = TD['old']
    else:
        # insert or update
        row = TD['new']
        if row['role_status'] == 'approved':
            # approved so add an entry to bugzilla
            newaction = 'a'
        else:
            # no longer approved so remove the entry from bugzilla
            newaction = 'r'

    # Get the group id for fedorabugs
    result = plpy.execute("select id from groups where name = 'fedorabugs'", 1)
    if not result:
        # Danger Will Robinson!  A basic FAS group does not exist!
        plpy.error('Basic FAS group fedorabugs does not exist')
    # If this is not a fedorabugs role, no change needed
    if row['group_id'] != result[0]['id']:
        return None

    # Retrieve the bugzilla email address
    ### FIXME: Once we implement it, we will want to add a check for an email
    # address in configs::application='bugzilla',person_id=person_id,
    # attribute='login'
    plan = plpy.prepare("select email from people where id = $1", ('int4',))
    result = plpy.execute(plan, (row['person_id'],))
    if not result:
        # No email address so nothing can be done
        return None
    email = result[0]['email']

    # If there is already a row in bugzilla_queue update, otherwise insert
    plan = plpy.prepare("select email from bugzilla_queue where email = $1",
            ('text',))
    result = plpy.execute(plan, (email,), 1)
    if result:
        plan = plpy.prepare("update bugzilla_queue set action = $1"
                " where email = $2", ('char', 'text'))
        plpy.execute(plan, (newaction, email))
    else:
        plan = plpy.prepare("insert into bugzilla_queue (email, group_id"
            ", person_id, action) values ($1, $2, $3, $4)",
                ('text', 'int4', 'int4', 'char'))
        plpy.execute(plan, (email, row['group_id'], row['person_id'], newaction))
    return None
$bz_sync$ language plpythonu;

create trigger role_bugzilla_sync before update or insert or delete
  on person_roles
  for each row execute procedure bugzilla_sync();

--
-- When an email address changes, check whether it needs to be changed in
-- bugzilla as well.
--
create or replace function bugzilla_sync_email() returns trigger AS $bz_sync_e$
    if TD['old']['email'] == TD['new']['email']:
        # We only care if the email has been changed
        return None;

    # Get the group id for fedorabugs
    result = plpy.execute("select id from groups where name = 'fedorabugs'", 1)
    if not result:
        # Danger Will Robinson!  A basic FAS group does not exist!
        plpy.error('Basic FAS group fedorabugs does not exist')
    fedorabugsId = result[0]['id']

    plan = plpy.prepare("select person_id from person_roles where"
        " role_status = 'approved' and group_id = $1 "
        " and person_id = $2", ('int4', 'int4'))
    result = plpy.execute(plan, (fedorabugsId, TD['old']['id']), 1)
    if not result:
        # We only care if Person belongs to fedorabugs
        return None;

    # Remove the old Email and add the new one
    changes = []
    changes.append((TD['old']['email'], fedorabugsId, TD['old']['id'], 'r'))
    changes.append((TD['new']['email'], fedorabugsId, TD['new']['id'], 'a'))

    for change in changes:
        # Check if we already have a pending change
        plan = plpy.prepare("select b.email from bugzilla_queue as b where"
            " b.email = $1", ('text',))
        result = plpy.execute(plan, (change[0],), 1)
        if result:
            # Yes, update that change
            plan = plpy.prepare("update bugzilla_queue set email = $1,"
                " group_id = $2, person_id = $3, action = $4 where "
                " email = $1", ('text', 'int4', 'int4', 'char'))
            plpy.execute(plan, change)
        else:
            # No, add a new change
            plan = plpy.prepare("insert into bugzilla_queue"
                " (email, group_id, person_id, action)"
                " values ($1, $2, $3, $4)", ('text', 'int4', 'int4', 'char'))
            plpy.execute(plan, change)

    return None
$bz_sync_e$ language plpythonu;

create trigger email_bugzilla_sync before update on people
  for each row execute procedure bugzilla_sync_email();

-- For Fas to connect to the database
GRANT ALL ON TABLE people, groups, person_roles, bugzilla_queue, configs, configs_id_seq, person_seq, visit, visit_identity, log, log_id_seq, session TO GROUP fedora;

-- Create default admin user - Default Password "admin"
INSERT INTO people (id, username, human_name, password, email) VALUES (100001, 'admin', 'Admin User', '$1$djFfnacd$b6NFqFlac743Lb4sKWXj4/', 'root@localhost');

-- Create default groups and populate
INSERT INTO groups (id, name, display_name, owner_id, group_type, user_can_remove) VALUES (100002, 'cla_done', 'CLA Done Group', (SELECT id from people where username='admin'), 'cla', false);
INSERT INTO groups (id, name, display_name, owner_id, group_type, user_can_remove) VALUES (101441, 'cla_fedora', 'Fedora CLA Group', (SELECT id from people where username='admin'), 'cla', false);
INSERT INTO groups (id, name, display_name, owner_id, group_type) VALUES (100006, 'accounts', 'Account System Admins', (SELECT id from people where username='admin'), 'tracking');
INSERT INTO groups (id, name, display_name, owner_id, group_type) VALUES (100148, 'fedorabugs', 'Fedora Bugs Group', (SELECT id from people where username='admin'), 'tracking');
INSERT INTO groups (name, display_name, owner_id, group_type) VALUES ('fas-system', 'System users allowed to get password and key information', (SELECT id from people where username='admin'), 'system');


INSERT INTO person_roles (person_id, group_id, role_type, role_status, internal_comments, sponsor_id) VALUES ((SELECT id from people where username='admin'), (select id from groups where name='accounts'), 'administrator', 'approved', 'created at install time', (SELECT id from people where username='admin'));
