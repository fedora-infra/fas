Installing FreeIPA
==================

* Note: Currently only tested on F13 and newer

First download and install the rpms:
    $ sudo wget http://freeipa.org/downloads/freeipa-devel.repo -O /etc/yum.repos.d/freeipa-devel.repo
    $ sudo yum install ipa-server

Next make sure your DNS is working.  You should have forward and reverse lookup
in place prior to running ipa-server-install (below)

    $ sudo /usr/sbin/ipa-server-install


Installation and Setup
======================

Install ``fas`` using the setup.py script::

    $ cd fas
    $ python setup.py build

Create the project database for any model classes defined::

    $ paster setup-app development.ini

Start the paste http server::

    $ paster serve development.ini

While developing you may want the server to reload after changes in package files (or its dependencies) are saved. This can be achieved easily by adding the --reload option::

    $ paster serve --reload development.ini

Then you are ready to go.
