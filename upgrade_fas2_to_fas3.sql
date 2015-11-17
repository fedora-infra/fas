-- Drop un-used tables

DROP TABLE session;
DROP TABLE migration_version;
DROP TABLE visit;
DROP TABLE vistit_identity;
DROP TABLE configs;
DROP TABLE requests;
DROP TABLE samadhi_associations;
DROP TABLE samadhi_nonces;
DROP TABLE group_roles;


-- Create new tables, specific for FAS3

CREATE TABLE account_permissions
(
  id serial NOT NULL,
  people integer NOT NULL,
  token text NOT NULL,
  application text NOT NULL,
  permissions integer NOT NULL,
  granted_timestamp timestamp without time zone NOT NULL,
  last_used timestamp without time zone,
  CONSTRAINT account_permissions_pkey PRIMARY KEY (id),
  CONSTRAINT account_permissions_people_fkey FOREIGN KEY (people)
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
  creation_timestamp timestamp without time zone NOT NULL,
  CONSTRAINT certificates_pkey PRIMARY KEY (id)
)
WITH (
  OIDS=FALSE
);

CREATE TABLE clients_certificates
(
  id serial NOT NULL,
  ca integer,
  people integer,
  serial integer,
  certificate text,
  CONSTRAINT clients_certificates_pkey PRIMARY KEY (id),
  CONSTRAINT clients_certificates_ca_fkey FOREIGN KEY (ca)
      REFERENCES certificates (id) MATCH SIMPLE
      ON UPDATE NO ACTION ON DELETE NO ACTION,
  CONSTRAINT clients_certificates_people_fkey FOREIGN KEY (people)
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
  creation_timestamp timestamp without time zone NOT NULL,
  update_timestamp timestamp without time zone NOT NULL,
  CONSTRAINT license_agreement_pkey PRIMARY KEY (id)
)
WITH (
  OIDS=FALSE
);

CREATE TABLE people_activity_log
(
  id serial NOT NULL,
  people integer NOT NULL,
  location text NOT NULL,
  remote_ip character varying NOT NULL,
  access_from text NOT NULL,
  event integer NOT NULL,
  event_msg text,
  "timestamp" timestamp without time zone,
  CONSTRAINT people_activity_log_pkey PRIMARY KEY (id),
  CONSTRAINT people_activity_log_people_fkey FOREIGN KEY (people)
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
  license integer,
  people integer,
  signed boolean NOT NULL,
  CONSTRAINT signed_license_agreement_pkey PRIMARY KEY (id),
  CONSTRAINT signed_license_agreement_license_fkey FOREIGN KEY (license)
      REFERENCES license_agreement (id) MATCH SIMPLE
      ON UPDATE NO ACTION ON DELETE NO ACTION,
  CONSTRAINT signed_license_agreement_people_fkey FOREIGN KEY (people)
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
  granted_timestamp timestamp without time zone NOT NULL,
  last_used timestamp without time zone,
  CONSTRAINT trusted_perms_pkey PRIMARY KEY (id)
)
WITH (
  OIDS=FALSE
);

CREATE TABLE virtual_people
(
  id serial NOT NULL,
  username text NOT NULL,
  parent integer NOT NULL,
  type integer,
  last_logged timestamp without time zone,
  CONSTRAINT virtual_people_pkey PRIMARY KEY (id),
  CONSTRAINT virtual_people_parent_fkey FOREIGN KEY (parent)
      REFERENCES people (id) MATCH SIMPLE
      ON UPDATE NO ACTION ON DELETE NO ACTION,
  CONSTRAINT virtual_people_username_key UNIQUE (username)
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


-- Adjust the people table for FAS3

ALTER TABLE people ADD avatar_id character varying;
ALTER TABLE people ADD introduction text;
ALTER TABLE people ADD birthday integer;
ALTER TABLE people ADD birthday_month text;
ALTER TABLE people ADD bio text;
ALTER TABLE people ADD gpg_fingerprint text;
ALTER TABLE people ADD recovery_email text;
ALTER TABLE people ADD bugzilla_email text;
ALTER TABLE people ADD login_attempt integer;
ALTER TABLE people ADD github_token text;
ALTER TABLE people ADD fas_token text;
ALTER TABLE people ADD twitter_token text;


ALTER TABLE people RENAME COLUMN human_name to fullname;
ALTER TABLE people RENAME COLUMN blog_avatar to avatar;
ALTER TABLE people RENAME COLUMN gpg_keyid to gpg_id;
ALTER TABLE people RENAME COLUMN emailtoken to email_token;
ALTER TABLE people RENAME COLUMN passwordtoken to password_token;
ALTER TABLE people RENAME COLUMN last_seen to last_logged;


ALTER TABLE people ADD CONSTRAINT people_bugzilla_email_key UNIQUE (bugzilla_email);
ALTER TABLE people ADD CONSTRAINT people_email_token_key UNIQUE (email_token);
ALTER TABLE people ADD CONSTRAINT people_ircnick_key UNIQUE (ircnick);
ALTER TABLE people ADD CONSTRAINT people_recovery_email_key UNIQUE (recovery_email);


-- Adjust the groups table for FAS3

ALTER TABLE groups ADD description text;
ALTER TABLE groups ADD status integer;
ALTER TABLE groups ADD avatar text;
ALTER TABLE groups ADD private boolean;
ALTER TABLE groups ADD require_ssh boolean;
ALTER TABLE groups ADD bound_to_github boolean;
ALTER TABLE groups ADD license_sign_up integer;
ALTER TABLE groups ADD certificate integer;
ALTER TABLE groups ADD updated timestamp without time zone NOT NULL;


ALTER TABLE groups RENAME COLUMN url to web_link;
ALTER TABLE groups RENAME COLUMN joinmsg to join_msg;
ALTER TABLE groups RENAME COLUMN creation to created;


ALTER TABLE groups ADD CONSTRAINT group_certificate_fkey FOREIGN KEY (certificate)
      REFERENCES certificates (id) MATCH SIMPLE
      ON UPDATE NO ACTION ON DELETE NO ACTION;
ALTER TABLE groups ADD CONSTRAINT group_group_type_fkey FOREIGN KEY (group_type)
      REFERENCES group_type (id) MATCH SIMPLE
      ON UPDATE NO ACTION ON DELETE NO ACTION;
ALTER TABLE groups ADD CONSTRAINT group_license_sign_up_fkey FOREIGN KEY (license_sign_up)
      REFERENCES license_agreement (id) MATCH SIMPLE
      ON UPDATE NO ACTION ON DELETE NO ACTION;
ALTER TABLE groups ADD CONSTRAINT group_owner_id_fkey FOREIGN KEY (owner_id)
      REFERENCES people (id) MATCH SIMPLE
      ON UPDATE NO ACTION ON DELETE NO ACTION;
ALTER TABLE groups ADD CONSTRAINT group_parent_group_id_fkey FOREIGN KEY (parent_group_id)
      REFERENCES groups (id) MATCH SIMPLE
      ON UPDATE NO ACTION ON DELETE NO ACTION;


-- Adjust the person_roles table for FAS3
ALTER TABLE person_roles RENAME TO group_membership;

ALTER TABLE group_membership ADD COLUMN role integer;
ALTER TABLE group_membership ADD COLUMN status integer;

ALTER TABLE group_membership RENAME COLUMN person_id to people_id;
ALTER TABLE group_membership RENAME COLUMN sponsor_id to sponsor;
ALTER TABLE group_membership RENAME COLUMN creation to creation_timestamp;
ALTER TABLE group_membership RENAME COLUMN approval to approval_timestamp;
