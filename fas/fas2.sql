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
    passwordtoken text null,
    comments TEXT,
    postal_address TEXT,
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
    check (status in ('active', 'vacation', 'inactive', 'pinged'))
    --check (gpg_keyid ~ '^[0-9A-F]{17}$')
);

create index people_status_idx on people(status);
cluster people_status_idx on people;

CREATE TABLE person_emails (
    id serial primary key,
    email text not null unique,
    person_id INTEGER NOT NULL references people(id),
    validtoken text,
    description text,
    verified boolean NOT NULL DEFAULT false
);

create index person_emails_person_id_idx on person_emails(person_id);
cluster person_emails_person_id_idx on person_emails;

CREATE TABLE email_purposes (
    email_id INTEGER NOT NULL references person_emails(id),
    person_id INTEGER NOT NULL references people(id),
    purpose text NOT NULL,
    primary key (person_id, purpose),
    check (purpose ~ ('(bugzilla|primary|cla|pending|other[0-9]+)'))
);

create index email_purposes_email_id_idx on email_purposes(email_id);
create index email_purposes_person_id_idx on email_purposes(person_id);
cluster email_purposes_person_id_idx on email_purposes;

CREATE TABLE configs (
    id SERIAL PRIMARY KEY,
    person_id integer references people(id),
    application TEXT not null,
    attribute TEXT not null,
    -- The value should be a simple value or a json string.
    -- Please create more config keys rather than abusing this with
    -- large datastructures.
    value TEXT,
    check (application in ('asterisk', 'moin', 'myfedora' ,'openid'))
    -- Might end up removing openid, depending on how far we take the provider
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
    owner_id INTEGER NOT NULL REFERENCES people(id),
    group_type VARCHAR(16),
    needs_sponsor BOOLEAN DEFAULT FALSE,
    user_can_remove BOOLEAN DEFAULT TRUE,
    prerequisite_id INTEGER REFERENCES groups(id),
    joinmsg TEXT NULL DEFAULT '',
    -- tg_group::created
    creation TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    check (group_type in ('bugzilla','cvs', 'bzr', 'git', 'hg', 'mtn',
        'svn', 'shell', 'torrent', 'tracker', 'tracking', 'user')) 
);

create index groups_group_type_idx on groups(group_type);
cluster groups_group_type_idx on groups;

--
-- Group Emails are slightly different than person emails.
-- We are much more relaxed about email "ownership".  A group can share an
-- email address with another group.  (For instance, xen-maint and
-- kernel-maint might share the same email address for mailing list and
-- bugzilla.
--
CREATE TABLE group_emails (
    id serial primary key,
    email text not null unique,
    group_id INTEGER NOT NULL references groups(id),
    validtoken text,
    description text,
    verified boolean NOT NULL DEFAULT false
);

create index group_emails_group_id_idx on group_emails(group_id);
cluster group_emails_group_id_idx on group_emails;

CREATE TABLE group_email_purposes (
    email_id INTEGER NOT NULL references group_emails(id),
    group_id INTEGER NOT NULL references groups(id),
    purpose text NOT NULL,
    primary key (group_id, purpose),
    check (purpose ~ ('(bugzilla|primary|mailing list|other[0-9]+)'))
);

create index group_email_purposes_email_id_idx on group_email_purposes(email_id);
create index group_email_purposes_person_id_idx on group_email_purposes(group_id);
cluster group_email_purposes_person_id_idx on group_email_purposes;

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

CREATE TABLE group_roles (
    member_id INTEGER NOT NULL REFERENCES groups(id),
    group_id INTEGER NOT NULL REFERENCES groups(id),
    role_type text NOT NULL,
    role_status text DEFAULT 'unapproved',
    internal_comments text,
    sponsor_id INTEGER REFERENCES people(id),
    creation TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    approval TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    primary key (member_id, group_id),
    check (role_status in ('approved', 'unapproved')),
    check (role_type in ('user', 'administrator', 'sponsor'))
);

create index group_roles_member_id_idx on group_roles(member_id);
create index group_roles_group_id_idx on group_roles(group_id);
-- We could cluster on either member or group.  The choice of member is
-- because member pages will be viewed more frequently.
-- Open to reevaluation.
cluster group_roles_group_id_idx on group_roles;

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
    user_id INTEGER references people(id)
);

--
-- When a person's fedorabugs role is updated, add them to bugzilla queue.
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
    plan = plpy.prepare("select email, purpose from person_emails as pee,"
            " email_purposes as epu"
            " where epu.id = epu.email_id and pee.person_id = $1"
            " and purpose in ('bugzilla', 'primary')",
            ('text',))
    result = plpy.execute(plan, row['person_id'])
    email = None
    for record in result:
        email = record['email']
        if record['purpose'] == 'bugzilla':
            break
    if not email:
        raise plpy.error('Cannot approve fedorabugs for person_id(%s) because they have no email address to use with bugzilla' % row['person_id'])

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
                ('text', 'text', 'text', 'char'))
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
--  create or replace function bugzilla_sync_email() returns trigger AS $bz_sync_e$
--      # To port this we need to operate on two tables now
--      if TD['event'] == 'DELETE':
--          row = TD['old']
--      else:
--          row = TD['new']
--  
--      if TD['event'] == 'UPDATE':
--          if TD['old']['email'] == TD['new']['email']:
--              # Email has not changed.  We do not care
--              return None
--      if row['purpose'] not in ('bugzilla', 'primary'):
--          # The change is to an email address that does not affect bugzilla
--          return None
--      elif row['purpose'] == 'primary':
--          # Check if there is a better email.
--          plan = plpy.prepare("select email from person_emails where"
--                  " purpose = 'bugzilla' and person_id = $1", ('text',))
--          result = plpy.execute(plan, (row['person_id'],), 1)
--          if result:
--              # If the change is to primary but there is a bugzilla address, it
--              # will have no effect.
--              return None
--      # Check that the person belongs to fedorabugs
--      plan = plpy.prepare("select * from people as p, person_roles as r,"
--              " groups as g where p.id = r.person_id and r.group_id = g.id"
--              " and r.role_status = 'approved' and g.name = 'fedorabugs'"
--              " and p.id = $1", ('text',))
--      result = plpy.execute(plan, (row['person_id'],), 1)
--      if not result:
--          # Person does not belong to fedorabugs so this will have no effect.
--          return None
--  
--      # We now know that we have changes to make
--    
--      #
--      # Remove the old Email address
--      #
--      oldEmail = None
--      if TD['event'] in ('DELETE', 'UPDATE'):
--          oldEmail = TD['old']['email']
--      elif row['purpose'] == 'bugzilla':
--          # Insert: check if there is an email for primary that this email is
--          # superceding
--          plan = plpy.prepare("select email from person_emails"
--                  " where purpose = 'primary' and person_id = $1", ('text',))
--          result = plpy.execute(plan, (row['person_id'],), 1)
--          if result:
--              oldEmail = result[0]['email']
--  
--      if oldEmail:
--          plan = plpy.prepare("select email from bugzilla_queue where email = $1",
--                  ('text',))
--          result = plpy.execute(plan, oldEmail, 1)
--          if result:
--              plan = plpy.prepare("update bugzilla_queue set action = 'r'"
--                      " where email = $1", ('text',))
--              plpy.execute(plan, (oldEmail))
--          else:    
--              plan = plpy.prepare("insert into bugzilla_queue () values(email"
--                      ", group_id, person_id, action) values ($1, $2, $3, 'r')",
--                      ('text', 'text', 'text'))
--              plpy.execute(plan, (oldEmail, row['group_id'], row['person_id']))
--  
--      #
--      # Add a new email address to bugzilla
--      #
--      newEmail = None
--      if TD['event'] in ('INSERT', 'UPDATE'):
--          newEmail = TG['new']
--      elif row['purpose'] == 'bugzilla':
--          # When deleting a bugzilla email, check if there is a primary to
--          # fallback on
--          plan = plpy.prepare("select email from person_emails"
--                  " where purpose = 'primary' and person_id = $1", ('text',))
--          result = plpy.execute(plan, (row['person_id'],), 1)
--          if result:
--              newEmail = result[0]['email']
--  
--      if newEmail:
--          plan = plpy.prepare("select email from bugzilla_queue where email = $1",
--                  ('text',))
--          result = plpy.execute(plan, newEmail, 1)
--          if result:
--              plan = plpy.prepare("update bugzilla_queue set action = 'a'"
--                      " where email = $1", ('text',))
--              plpy.execute(plan, (newEmail))
--          else:    
--              plan = plpy.prepare("insert into bugzilla_queue () values(email"
--                      ", group_id, person_id, action) values ($1, $2, $3, 'a')",
--                      ('text', 'text', 'text'))
--              plpy.execute(plan, (newEmail, row['group_id'], row['person_id']))
--      return None
--  $bz_sync_e$ language plpythonu;
--  
--  create trigger email_bugzilla_sync before update or insert or delete
--   on person_emails
--   for each row execute procedure bugzilla_sync_email();

-- For Fas to connect to the database
GRANT ALL ON TABLE people, groups, person_roles, person_emails, email_purposes, group_roles, group_emails, group_email_purposes, bugzilla_queue, configs, person_seq, visit, visit_identity, log, log_id_seq, person_emails_id_seq, group_emails_id_seq TO GROUP fedora;

-- Create default admin user - Default Password "admin"
INSERT INTO people (username, human_name, password) VALUES ('admin', 'Admin User', '$1$djFfnacd$b6NFqFlac743Lb4sKWXj4/');

-- Create default groups and populate
INSERT INTO groups (name, display_name, owner_id, group_type) VALUES ('cla_sign', 'Signed CLA Group', (SELECT id from people where username='admin'), 'tracking');
INSERT INTO groups (name, display_name, owner_id, group_type) VALUES ('cla_click', 'Click-through CLA Group', (SELECT id from people where username='admin'), 'tracking');
INSERT INTO groups (name, display_name, owner_id, group_type) VALUES ('accounts', 'Account System Admins', (SELECT id from people where username='admin'), 'tracking');
INSERT INTO groups (name, display_name, owner_id, group_type) VALUES ('fedorabugs', 'Fedora Bugs Group', (SELECT id from people where username='admin'), 'tracking');

INSERT INTO person_roles (person_id, group_id, role_type, role_status, internal_comments, sponsor_id) VALUES ((SELECT id from people where username='admin'), (select id from groups where name='accounts'), 'administrator', 'approved', 'created at install time', (SELECT id from people where username='admin'));

-- Give admin user his email address
INSERT INTO person_emails (email, person_id, verified) VALUES ('root@localhost', (SELECT id from people where username='admin'), true);
INSERT INTO email_purposes (email_id, person_id, purpose) VALUES ((SELECT id from person_emails where email='root@localhost'), (SELECT id from people where username='admin'), 'primary');
