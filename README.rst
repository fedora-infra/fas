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

Add the following to your `~/.zshrc`::

    export WORKON_HOME=$HOME/.virtualenvs
    source /usr/bin/virtualenvwrapper.sh

Bootstrap the virtualenv
------------------------
::

    ./bootstrap.py
    workon fas-python2.7

Run the test suite
------------------
``python setup.py test``

Initialize the database
-----------------------
``initialize_fas_db``

Migrating FAS from release 2.x
---------------------------------
::

    work in progress


Run the web app
---------------
``pserve development.ini --reload``



