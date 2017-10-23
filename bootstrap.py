#!/usr/bin/env python
""" This script can bootstrap either a python2 or a python3 environment.

The environments it generates are named by the python version they are built
against.  i.e.:  fas-python2.7 or fas-python3.2.
To generate one or the other, just use the relevant python binary.  For a
python2 env, run::

    python2 bootstrap.py

And for a python3 env, run::

    python3 bootstrap.py
"""

import subprocess
import shutil
import sys
import os

ENVS = os.path.expanduser('~/.virtualenvs')
VENV = 'fas-python{major}.{minor}'.format(
    major=sys.version_info.major,
    minor=sys.version_info.minor,
)


def _link_system_lib(lib, virtenv_dir):
    for libdir in ('lib', 'lib64'):
        location = '{libdir}/python{major}.{minor}/site-packages'.format(
            major=sys.version_info.major, minor=sys.version_info.minor,
            libdir=libdir)
        if not os.path.exists(os.path.join('/usr', location, lib)):
            if os.path.exists(os.path.join('/usr', location, lib + '.so')):
                lib += '.so'
            elif os.path.exists(os.path.join('/usr', location, lib + '.py')):
                lib += '.py'
            else:
                continue
        template = 'ln -s /usr/{location}/{lib} {workon}/{venv}/{location}/'
        print("Linking in global module: %s" % lib)
        cmd = template.format(
            location=location, venv=VENV, lib=lib,
            workon=virtenv_dir)
        try:
            subprocess.check_output(cmd.split())
            return True
        except subprocess.CalledProcessError as e:
            # File already linked.
            return e.returncode == 256

    print("Cannot find global module %s" % lib)


def link_system_libs(virtenv_dir):
    sys_libs = ['sqlitecachec', '_sqlitecache', 'psycopg2', 'krbVmodule']
    for mod in sys_libs:
        _link_system_lib(mod, virtenv_dir)


def _do_virtualenvwrapper_command(cmd):
    """ This is tricky, because all virtualenwrapper commands are
    actually bash functions, so we can't call them like we would
    other executables.
    """
    print("Trying '%s'" % cmd)
    out, err = subprocess.Popen(
        ['bash', '-c', '. /usr/bin/virtualenvwrapper.sh; %s' % cmd],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    ).communicate()
    print(out)
    print(err)


def rebuild():
    """ Completely destroy and rebuild the virtualenv. """
    try:
        _do_virtualenvwrapper_command('rmvirtualenv %s' % VENV)
    except Exception as e:
        print(unicode(e))

    cmd = 'mkvirtualenv --no-site-packages -p /usr/bin/python{major}.{minor} {v}'\
            .format(
                major=sys.version_info.major,
                minor=sys.version_info.minor,
                v=VENV,
            )
    _do_virtualenvwrapper_command(cmd)

    # Do two things here:
    #  - remove all *.pyc that exist in srcdir.
    #  - remove all data/templates dirs that exist (mako caches).
    for base, dirs, files in os.walk(os.getcwd()):
        for fname in files:
            if fname.endswith(".pyc"):
                os.remove(os.path.sep.join([base, fname]))

        if base.endswith('data/templates'):
            shutil.rmtree(base)


def setup_develop(virtenv_dir):
    """ `python setup.py develop` in our virtualenv """
    # Disable easy_install way (egg file) install
    # cmd = '{workon}/{env}/bin/python setup.py develop'.format(
    #     envs=ENVS, env=VENV, workon=os.getenv("WORKON_HOME"))
    # Use pip way to install into our virtualenv as we have
    # on dependency which doesn't work as expected when install as egg file
    cmd = '{workon}/{env}/bin/pip install -e .'.format(
        envs=ENVS, env=VENV, workon=virtenv_dir)
    print(cmd)
    subprocess.call(cmd.split())


if __name__ == '__main__':
    virtenv_dir = os.getenv('WORKON_HOME')
    
    if virtenv_dir is None:
        print('ERROR: Cannot bootstrap FAS, your virtual-env dir is not set'
              'Please, set variable "WORKON_HOME" wiith your virtual-env '
              'root dir value.')
        sys.exit(1)

    print("Bootstrapping fas...")
    rebuild()
    link_system_libs(virtenv_dir)
    setup_develop(virtenv_dir)
