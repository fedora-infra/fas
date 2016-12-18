FAS (Fedora Account System) 3.0
===============================

:Authors:   Xavier Lamien

.. startdesc

The Fedora Account System is a community oriented accounts system which
aims to provide a self-driven and self-controled management to its registered users.

.. enddesc

.. contents::

.. startinstall

Requirements
------------

Packages
~~~~~~~~

* `pyramid`_ (1.5.1 or newer)
* `pyramid_mako`_
* `SQLAlchemy`_ (1.0 or newer)
* `transaction`_
* `pyramid_tm`_
* `zope.sqlalchemy`_
* `waitress`_
* `pytz`_
* `enum34`_
* `wtforms`_
* `mistune`_
* `GeoIP`_
* `pygeoip`_
* `ua-parser`_
* `pyyaml`_
* `pillow`_
* `cryptography`_
* `Babel`_
* `lingua`_
* `fedmsg`_
* `PyGithub`_ (optional)
* `fake-factory`_ (optional)
* `pyramid_debugtoolbar`_ (optional)

.. _`pyramid`: https://pypi.python.org/pypi/pyramid
.. _`pyramid_mako`: https://pypi.python.org/pypi/pyramid_mako
.. _`SQLAlchemy`: http://www.sqlalchemy.org/
.. _`transaction`: https://pypi.python.org/pypi/transaction/
.. _`pyramid_tm`: https://pypi.python.org/pypi/pyramid_tm/
.. _`waitress`: https://pypi.python.org/pypi/waitress/
.. _`wtforms`: https://pypi.python.org/pypi/wtforms/
.. _`mistune`: https://pypi.python.org/pypi/mistune/
.. _`GeoIP`: https://pypi.python.org/pypi/GeoIP/
.. _`pygeoip`: https://pypi.python.org/pypi/pygeoip/
.. _`ua-parser`: https://pypi.python.org/pypi/ua-parser/
.. _`pyyaml`: https://pypi.python.org/pypi/pyyaml/
.. _`pillow`: https://pypi.python.org/pypi/pillow/
.. _`cryptography`: https://pypi.python.org/pypi/cryptography/
.. _`Babel`: https://pypi.python.org/pypi/Babel/
.. _`lingua`: https://pypi.python.org/pypi/lingua/
.. _`fedmsg`: https://pypi.python.org/pypi/fedmsg/
.. _`PyGithub`: https://pypi.python.org/pypi/PyGithub/
.. _`zope.sqlalchemy`: https://pypi.python.org/pypi/zope.sqlalchemy
.. _`enum34`: https://pypi.python.org/pypi/enum-compat/0.0.2
.. _`pytz`: https://pypi.python.org/pypi/pytz
.. _`fake-factory`: https://pypi.python.org/pypi/fake-factory/
.. _`pyramid_debugtoolbar`: https://pypi.python.org/pypi/pyramid_debugtoolbar/

Python Version
~~~~~~~~~~~~~~

FAS has been tested on Python 2.6 and 2.7 only at this time.

Installation
------------

FAS can be installed as follows::

    % python setup.py install

If necessary, the ``--install-data`` option can be used to configure
the location in which the resources (``res``) and example·
files (``docs``) should be installed.

.. endinstall

Migrating FAS from release 2.x
---------------------------------
.. note:: work in progress

Getting involved
----------------
.. startdevsetup


Requirements
~~~~~~~~~~~~

* `virtualenvwrapper`_
* `libffi`_
* `openssl`_
* `GeoIP`_
* `libyaml`_

If you want to enable fonts that match with Fedora logo usage guideline:

* `comfortaa-fonts`_
* `cantarell-fonts`_

If you are running a Fedora or RedHat/CentOs's OS, here are dependencies'
packages to install::

    % sudo dnf install -y python-virtualenvwrapper libffi-devel openssl-devel \
            GeoIP-devel libyaml-devel redhat-rpm-config libjpeg-turbo-devel

Configuration
~~~~~~~~~~~~~
Add the following to your `~/.zshrc` or `~/.bashrc`::

    % export WORKON_HOME=$HOME/.virtualenvs
    % source /usr/bin/virtualenvwrapper.sh

and reload your shell by sourcing its rc's file or closing and opening your terminal back up.


And if you want to use system fonts::

    % sudo dnf install -y aajohan-comfortaa-fonts abattis-cantarell-fonts

Then run the boostrap helper script::

    % ./bootstrap.py

And finally, load the virtualenv created::

    % workon fas-python2.7


Initialize the database
~~~~~~~~~~~~~~~~~~~~~~~
``% fas-admin -c development.ini --initdb --default-value``

.. _`virtualenvwrapper`: https://pypi.python.org/pypi/virtualenvwrapper
.. _`libffi`: https://sourceware.org/libffi/
.. _`openssl`: https://www.openssl.org/
.. _`GeoIP`: http://www.maxmind.com/app/c
.. _`libyaml`: http://pyyaml.org/wiki/LibYAML
.. _`comfortaa-fonts`: http://www.dafont.com/comfortaa.font
.. _`cantarell-fonts`: https://www.fontsquirrel.com/fonts/cantarell
.. enddevsetup

Run the test suite
------------------

``% python setup.py test``

Add fake data (People and group)
--------------------------------
``% fas-admin -c development.ini --generate-fake-data -n 1200``

Run the web app
---------------
``% pserve development.ini --reload``

