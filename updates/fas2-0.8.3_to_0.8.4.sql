-- Copyright © 2008  Red Hat, Inc. All rights reserved.
-- Copyright © 2008  Ricky Zhou All rights reserved.
-- Copyright © 2008  Xavier Lamien All rights reserved.
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
-- Author(s): Ricky Zhou, Xavier Lamien, Toshio Kuratomi
--
--

-- Add new column to table <groups>
ALTER TABLE groups add column url TEXT;
ALTER TABLE groups add column mailing_list TEXT;
ALTER TABLE groups add column mailing_list_url TEXT;
ALTER TABLE groups add column irc_channel TEXT;
ALTER TABLE groups add column irc_network TEXT;

-- Add new column to table <people>
ALTER TABLE people add column country_code CHAR(2);


-- Add View for mod_auth_pgsql
CREATE VIEW user_group AS SELECT username, name AS groupname FROM people AS p, groups AS g, person_roles AS r WHERE r.person_id=p.id AND r.group_id=g.id AND r.role_status='approved';


-- Add new TuboGears session table

CREATE TABLE session (id VARCHAR(40) primary key, data text, expiration_time timestamp);

