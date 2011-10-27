-- Copyright © 2011  Red Hat, Inc.
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
-- Author(s): Toshio Kuratomi


-- Add the cla_fpca group to phase out the fedora_cla group
insert into groups (name, display_name, owner_id, group_type, invite_only, url) values ('cla_fpca', 'Signers of the Fedora Project Contributor Agreement', 100001, 'cla', true, 'http://fedoraproject.org/wiki/Legal:Fedora_Project_Contributor_Agreement');

-- Change schema so that the group_type is mandatory
alter table groups ALTER COLUMN group_type set not null;
