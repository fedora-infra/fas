-- Drop un-used tables

DROP TABLE IF EXISTS session;
DROP TABLE IF EXISTS migrate_version;
DROP TABLE IF EXISTS visit_identity;
DROP TABLE IF EXISTS visit;
DROP TABLE IF EXISTS configs;
DROP TABLE IF EXISTS requests;
DROP TABLE IF EXISTS samadhi_associations;
DROP TABLE IF EXISTS samadhi_nonces;
DROP TABLE IF EXISTS group_roles;

DROP VIEW IF EXISTS user_group;

-- Create new tables, specific for FAS3

CREATE TABLE account_permissions
(
  id serial NOT NULL,
  person_id integer NOT NULL,
  token text NOT NULL,
  application text NOT NULL,
  permissions integer NOT NULL,
  granted_timestamp timestamp with time zone NOT NULL,
  last_used_timestamp timestamp with time zone,
  CONSTRAINT account_permissions_pkey PRIMARY KEY (id),
  CONSTRAINT account_permissions_person_id_fkey FOREIGN KEY (person_id)
      REFERENCES people (id) MATCH SIMPLE
      ON UPDATE NO ACTION ON DELETE NO ACTION,
  CONSTRAINT account_permissions_token_key UNIQUE (token)
)
WITH (
  OIDS=FALSE
);

CREATE TABLE certificates
(
  id serial NOT NULL,
  name character varying(255) NOT NULL,
  description text,
  cert text NOT NULL,
  cert_key text NOT NULL,
  client_cert_desc text NOT NULL,
  enabled boolean,
  creation_timestamp timestamp with time zone NOT NULL,
  CONSTRAINT certificates_pkey PRIMARY KEY (id)
)
WITH (
  OIDS=FALSE
);

CREATE TABLE people_certificates
(
  id serial NOT NULL,
  ca integer,
  person_id integer,
  serial integer,
  certificate text,
  CONSTRAINT people_certificates_pkey PRIMARY KEY (id),
  CONSTRAINT people_certificates_ca_fkey FOREIGN KEY (ca)
      REFERENCES certificates (id) MATCH SIMPLE
      ON UPDATE NO ACTION ON DELETE NO ACTION,
  CONSTRAINT people_certificates_person_id_fkey FOREIGN KEY (person_id)
      REFERENCES people (id) MATCH SIMPLE
      ON UPDATE NO ACTION ON DELETE NO ACTION
)
WITH (
  OIDS=FALSE
);

CREATE TABLE group_type
(
  id serial NOT NULL,
  name text NOT NULL,
  comment text,
  CONSTRAINT group_type_pkey PRIMARY KEY (id),
  CONSTRAINT group_type_name_key UNIQUE (name)
)
WITH (
  OIDS=FALSE
);

CREATE TABLE license_agreement
(
  id serial NOT NULL,
  name character varying(255) NOT NULL,
  status integer,
  content text NOT NULL,
  comment text,
  enabled_at_signup boolean,
  creation_timestamp timestamp with time zone NOT NULL,
  update_timestamp timestamp with time zone NOT NULL,
  CONSTRAINT license_agreement_pkey PRIMARY KEY (id)
)
WITH (
  OIDS=FALSE
);

CREATE TABLE people_activity_log
(
  id serial NOT NULL,
  person_id integer NOT NULL,
  location text NOT NULL,
  remote_ip character varying NOT NULL,
  access_from text NOT NULL,
  event integer NOT NULL,
  event_msg text,
  event_timestamp timestamp with time zone,
  CONSTRAINT people_activity_log_pkey PRIMARY KEY (id),
  CONSTRAINT people_activity_log_person_id_fkey FOREIGN KEY (person_id)
      REFERENCES people (id) MATCH SIMPLE
      ON UPDATE NO ACTION ON DELETE NO ACTION
)
WITH (
  OIDS=FALSE
);

CREATE TABLE plugins
(
  id serial NOT NULL,
  name character varying(255) NOT NULL,
  comment text,
  enabled boolean NOT NULL,
  CONSTRAINT plugins_pkey PRIMARY KEY (id)
)
WITH (
  OIDS=FALSE
);

CREATE TABLE signed_license_agreement
(
  id serial NOT NULL,
  license_id integer,
  person_id integer,
  CONSTRAINT signed_license_agreement_pkey PRIMARY KEY (id),
  CONSTRAINT signed_license_agreement_license_id_fkey FOREIGN KEY (license_id)
      REFERENCES license_agreement (id) MATCH SIMPLE
      ON UPDATE NO ACTION ON DELETE NO ACTION,
  CONSTRAINT signed_license_agreement_person_id_fkey FOREIGN KEY (person_id)
      REFERENCES people (id) MATCH SIMPLE
      ON UPDATE NO ACTION ON DELETE NO ACTION
)
WITH (
  OIDS=FALSE
);

CREATE TABLE trusted_perms
(
  id serial NOT NULL,
  application text NOT NULL,
  token text NOT NULL,
  secret text NOT NULL,
  permissions text NOT NULL,
  granted_timestamp timestamp with time zone NOT NULL,
  last_used_timestamp timestamp with time zone,
  CONSTRAINT trusted_perms_pkey PRIMARY KEY (id)
)
WITH (
  OIDS=FALSE
);


-- Create indexes

CREATE INDEX group_type_name_idx
  ON group_type
  USING btree
  (name COLLATE pg_catalog."default");

CREATE INDEX certificates_idx
  ON certificates
  USING btree
  (id);

CREATE INDEX account_access_log_idx
  ON people_activity_log
  USING btree
  (location COLLATE pg_catalog."default");

CREATE INDEX people_access_log_idx
  ON people_activity_log
  USING btree
  (access_from COLLATE pg_catalog."default");


-- --------------------------------
-- This is where the fun starts \ó/
-- --------------------------------

-- Insert statuses

INSERT INTO group_type (name) SELECT DISTINCT group_type FROM groups;


-- Adjust the people table for FAS3

ALTER TABLE people ADD avatar_id character varying;
ALTER TABLE people ADD introduction text;
ALTER TABLE people ADD birthday integer;
ALTER TABLE people ADD birthday_month text;
ALTER TABLE people ADD bio text;
ALTER TABLE people ADD recovery_email text;
ALTER TABLE people ADD bugzilla_email text;
ALTER TABLE people ADD login_attempt integer;
ALTER TABLE people ADD github_token text;
ALTER TABLE people ADD fas_token text;
ALTER TABLE people ADD twitter_token text;

ALTER TABLE people ADD update_timestamp timestamp with time zone;
UPDATE people SET update_timestamp = creation;
ALTER TABLE people ALTER COLUMN update_timestamp SET NOT NULL;

ALTER TABLE people DROP COLUMN comments;
ALTER TABLE people DROP COLUMN internal_comments;
ALTER TABLE people DROP COLUMN password_changed;

ALTER TABLE people RENAME COLUMN human_name to fullname;
ALTER TABLE people RENAME COLUMN blog_avatar to avatar;
ALTER TABLE people RENAME COLUMN gpg_keyid to gpg_fingerprint;
ALTER TABLE people RENAME COLUMN passwordtoken to password_token;
ALTER TABLE people RENAME COLUMN emailtoken to email_token;
ALTER TABLE people RENAME COLUMN creation to creation_timestamp;
ALTER TABLE people RENAME COLUMN last_seen to login_timestamp;
ALTER TABLE people RENAME COLUMN status_change to status_timestamp;
ALTER TABLE people RENAME COLUMN alias_enabled to email_alias;

-- Alter some of the existing fields
ALTER TABLE people ALTER COLUMN password TYPE text;
ALTER TABLE people ALTER COLUMN old_password TYPE text;

-- Change the status
ALTER TABLE people ADD COLUMN status2 integer;
UPDATE people SET status2 = 1 where status = 'active';
UPDATE people SET status2 = 6 where status = 'admin_disabled';
UPDATE people SET status2 = 2 where status = 'bot';
UPDATE people SET status2 = 0 where status = 'inactive';
UPDATE people SET status2 = 9 where status = 'spamcheck_awaiting';
UPDATE people SET status2 = 10 where status = 'spamcheck_denied';
UPDATE people SET status2 = 11 where status = 'spamcheck_manual';
ALTER TABLE people DROP COLUMN status;
ALTER TABLE people RENAME COLUMN status2 to status;

ALTER TABLE people ADD CONSTRAINT people_bugzilla_email_key UNIQUE (bugzilla_email);
--ALTER TABLE people ADD CONSTRAINT people_ircnick_key UNIQUE (ircnick);
ALTER TABLE people ADD CONSTRAINT people_recovery_email_key UNIQUE (recovery_email);

CREATE INDEX people_username_idx
  ON people
  USING btree
  (username COLLATE pg_catalog."default");


-- Adjust the groups table for FAS3

ALTER TABLE groups ADD description text;
ALTER TABLE groups ADD status integer;
ALTER TABLE groups ADD avatar text;
ALTER TABLE groups ADD private boolean;
ALTER TABLE groups ADD need_approval boolean;
ALTER TABLE groups ADD requires_ssh boolean;
ALTER TABLE groups ADD bound_to_github boolean;
ALTER TABLE groups ADD license_id integer;
ALTER TABLE groups ADD certificate_id integer;

ALTER TABLE groups ADD update_timestamp timestamp with time zone;
UPDATE groups SET update_timestamp = creation;
ALTER TABLE groups ALTER COLUMN update_timestamp SET NOT NULL;

ALTER TABLE groups ALTER COLUMN name TYPE varchar(40);

ALTER TABLE groups ADD group_type_id integer;
UPDATE groups SET group_type_id = group_type.id
    FROM group_type WHERE group_type.name = groups.group_type;
ALTER TABLE groups DROP COLUMN group_type;

UPDATE groups SET status = 1;

ALTER TABLE groups RENAME COLUMN needs_sponsor to requires_sponsorship;
ALTER TABLE groups RENAME COLUMN user_can_remove to self_removal;
ALTER TABLE groups RENAME COLUMN prerequisite_id to parent_group_id;
ALTER TABLE groups RENAME COLUMN joinmsg to join_msg;
ALTER TABLE groups RENAME COLUMN creation to creation_timestamp;
ALTER TABLE groups RENAME COLUMN url to web_link;

ALTER TABLE groups ADD CONSTRAINT groups_certificate_id_fkey FOREIGN KEY (certificate_id)
      REFERENCES certificates (id) MATCH SIMPLE
      ON UPDATE NO ACTION ON DELETE NO ACTION;
ALTER TABLE groups ADD CONSTRAINT groups_group_type_id_fkey FOREIGN KEY (group_type_id)
      REFERENCES group_type (id) MATCH SIMPLE
      ON UPDATE NO ACTION ON DELETE NO ACTION;
ALTER TABLE groups ADD CONSTRAINT groups_license_id_fkey FOREIGN KEY (license_id)
      REFERENCES license_agreement (id) MATCH SIMPLE
      ON UPDATE NO ACTION ON DELETE NO ACTION;
ALTER TABLE groups ADD CONSTRAINT groups_parent_group_id_fkey FOREIGN KEY (parent_group_id)
      REFERENCES groups (id) MATCH SIMPLE
      ON UPDATE NO ACTION ON DELETE NO ACTION;


-- Adjust the person_roles table for FAS3
ALTER TABLE person_roles RENAME TO group_membership;

ALTER TABLE group_membership ADD COLUMN id SERIAL NOT NULL;

ALTER TABLE group_membership ADD COLUMN role integer;
UPDATE group_membership SET role = 1 where role_type = 'user';
UPDATE group_membership SET role = 3 where role_type = 'sponsor';
UPDATE group_membership SET role = 4 where role_type = 'administrator';
ALTER TABLE group_membership DROP COLUMN role_type;

ALTER TABLE group_membership ADD COLUMN status integer;
UPDATE group_membership SET status = 1 where role_status = 'approved';
UPDATE group_membership SET status = 0 where role_status = 'unapproved';
ALTER TABLE group_membership DROP COLUMN role_status;

ALTER TABLE group_membership RENAME COLUMN internal_comments to comment;
ALTER TABLE group_membership RENAME COLUMN creation to creation_timestamp;
ALTER TABLE group_membership RENAME COLUMN approval to update_timestamp;




GRANT select,usage,update ON all sequences IN schema public to fedora;
GRANT select,update,insert ON all tables IN schema public to fedora;
GRANT usage ON schema public TO fedora;
