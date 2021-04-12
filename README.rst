=====================================
FAS no Longer developed or maintained
=====================================

The Fedora Account System (FAS2) is no longer developed or maintained. It was replaced in production in March 2021 by `Fedora Accounts <https://accounts.fedoraproject.org>`_. (which is actually comprised of many things, including `noggin <https://github.com/fedora-infra/noggin>`_, `freeipa-fas <https://github.com/fedora-infra/freeipa-fas>`_,  and `fasjson <https://github.com/fedora-infra/fasjson>`_).

FAS2 was launched in 2008, and when it was decomissioned in 2021, the final version used in production was FAS2 0.14.1 and looked like the following screenshot:

.. image:: https://docs.fedoraproject.org/en-US/fedora-accounts/_images/screenshots/fas2.png

----
FAS3
----

Around 2017, development was proceeding on FAS3, a complete re-write of FAS2. Ultimately, this project was not completed, and never reached production. This code is still availble in the FAS3 branch: https://github.com/fedora-infra/fas/tree/FAS3 

=====================
Fedora Account System
=====================

:Authors: Ricky Zhou
	  Mike McGrath
	  Toshio Kuratomi
	  Yaakov Nemoy
          Patrick Uiterwijk
:Contact: infrastructure@lists.fedoraproject.org
:Date: Wed, 26 March, 2008
:For FAS version: 0.8.x

The Fedora Account System holds information on Fedora Contributors to give
them access to the wonderful things that Fedora has.

.. contents::

This is a TurboGears_ project. It can be started by running the start-fas
script.

.. _TurboGears: http://www.turbogears.org

---------
Upgrading
---------

0.8.13 => 0.8.14
================

When upgrading to 0.8.14 the database schema changed slightly, and new
configuration options got introduced, for the security questions system.
The people table gets two new columns, for the question and answers, and
the configuration gets a new option to specify the key used to encrypt the
security answer. Apply the schema update like this:

sudo -u postgres psql fas2 < updates/fas2-0.8.13_to_0.8.14.sql

Also, the new key_securityquestion configuration parameter should be set
to the id of the key used to encrypt the answer to the security question.

Also, you should not forget to set deployment_type to the type of deployment
of this installation.

0.8.7 => 0.8.8
==============
We still haven't worked out using migrate scripts on our database servers so
the changes here need to be done like this:

  sudo -u postgres psql fas2 < updates/fas2-0.8.7_to_0.8.8.sql

0.8.5 => future
===============

From 0.8.5 and onward we will be using SQLAlchemy Migrate to handle database
upgrades.  To use it, it assumes you have already installed fas2.sql into your
posgresql database. The instructions for installing SQLAlchemy-Migrate on top
can be found below in the installation instructions.  

sqlalchemy-migrate will need to be installed.  To do so, run:

 sudo yum -y install python-migrate

(Since I don't trust this yet,  the latest change will need to add:
+    invite_only BOOLEAN DEFAULT FALSE,
to the groups table.  There is a migrate script checked in.  Need to verify
that it works and that we'll do that.)

0.8.4 => 0.8.5
==============

When upgrading to 0.8.5 the database schema changed slightly.  The configs
table now has a unique constraint to prevent duplicates being entered.  Use
this to update your existing schema::

  sudo -u postgres psql fas2 < updates/fas2-0.8.4_to_0.8.5.sql

0.8.3 => 0.8.4
==============

When upgrading from 0.8.3 to 0.8.4 there are some new database changes:

  :groups.url: URL where others can look for information about the group
  :groups.mailing_list: Specify a mailing list address that others can use to
  	contact the group
  :groups.mailing_list_url: A url where others can look at list archives and
  	sign up
  :groups.irc_network: IRC network on which the IRC channel is
  :groups.irc_channel: IRC channel where communication with the group occurs
  :people.country_code: Two digit country code for where the user is from
  :user_group: View that allows mod_auth_pgsql to work with the db
  :session: Table for doing OpenID sessions.

You can add these to your database by running the sql commands in
``updates/fas2-0.8.3_to_0.8.4.sql`` like this::

  sudo -u postgres psql fas2 < updates/fas2-0.8.3_to_0.8.4.sql

The country code functionality also makes use of python-GeoIP.  This should
be installed as a dependency if you use the fas rpms.  Otherwise you need to
install that manually::

  sudo yum -y install python-GeoIP
