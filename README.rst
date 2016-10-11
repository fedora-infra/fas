FAS (Fedora Account System) 3.0
===============================

:Authors:   Xavier Lamien

The Fedora Account System holds information on Fedora Contributors to give
them access to the wonderful things that Fedora has.

.. contents::

A Pyramid based project.


Setup virtualenvwrapper
-----------------------
``sudo yum -y install python-virtualenvwrapper``

Add the following to your `~/.zshrc` or `~/.bashrc`::

    export WORKON_HOME=$HOME/.virtualenvs
    source /usr/bin/virtualenvwrapper.sh

Once finished run this command `source ~/.zshrc` or `source ~/.bashrc` for which ever shell you use.

Bootstrap the virtualenv
------------------------
**Dependencies**

 - libffi
 - openssl
 - GeoIP
 - libyaml

If you want to enable fonts that match with Fedora logo usage guideline:

 - comfortaa-fonts
 - cantarell-fonts

Fedora OS

::

    sudo dnf install -y libffi-devel openssl-devel GeoIP-devel libyaml-devel redhat-rpm-config libjpeg-turbo-devel

    sudo dnf install -y aajohan-comfortaa-fonts abattis-cantarell-fonts
    # if you want to use system fonts

::

    ./bootstrap.py
    workon fas-python2.7

Run the test suite
------------------
``python setup.py test``
In root of the project

::

    workon fas-python2.7
    pip install pytest-cov
    python tests/runner.py

runner.py can take a cmd line argument `--db` which has options [local, faitout]::

    python tests/runner.py --db local
    ...
    python tests/runner.py --db faitout

open index.html from the cov_html

Initialize the database
-----------------------
``fas-admin -c development.ini --initdb [--default-value]``

Add fake data (People and group)
-------------------------------
``fas-admin -c development.ini --generate-fake-data [-n]``

Migrating FAS from release 2.x
---------------------------------
::

    work in progress


Run the web app
---------------
``pserve development.ini --reload``
