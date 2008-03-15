#!/usr/bin/python -tt

import os
import re
import glob

from distutils.command.build import build as _build
from distutils.command.install_data import install_data as _install_data
from distutils.dep_util import newer

from setuptools import setup, find_packages
from turbogears.finddata import find_package_data, standard_exclude, \
        standard_exclude_directories

execfile(os.path.join('fas', 'release.py'))

excludeFiles = ['*.cfg.in']
excludeFiles.extend(standard_exclude)
excludeDataDirs = ['fas/static']
excludeDataDirs.extend(standard_exclude_directories)

SUBSTFILES = ('fas/config/app.cfg',)

class Build(_build, object):
    '''
    Build the package, changing the directories that data files are installed.
    '''
    user_options = _build.user_options
    user_options.extend([('install-data=', None,
        'Installation directory for data files')])
    # These are set in finalize_options()
    substitutions = {'@DATADIR@': None}
    subRE = re.compile('(' + '|'.join(substitutions.keys()) + ')+')

    def initialize_options(self):
        self.install_data = None
        super(Build, self).initialize_options()

    def finalize_options(self):
        self.substitutions['@DATADIR@'] = self.install_data or \
                '%(top_level_dir)s'
        super(Build, self).finalize_options()

    def run(self):
        '''Substitute special variables for our installation locations.'''
        for filename in SUBSTFILES:
            # Change files to reference the data directory in the proper
            # location
            infile = filename + '.in'
            if not os.path.exists(infile):
                continue
            try:
                f = file(infile, 'r')
            except IOError:
                if not self.dry_run:
                    raise
                f = None
            outf = file(filename, 'w')
            for line in f.readlines():
                matches = self.subRE.search(line)
                if matches:
                    for pattern in self.substitutions:
                        line = line.replace(pattern, self.substitutions[pattern])
                outf.writelines(line)
            outf.close()
            f.close()
        super(Build, self).run()

### FIXME: This method breaks eggs.
# Unfortunately, instead of eggs being built by putting together package *.py
# files and data sanely at the last minute, they are built by putting them
# together in the build step.  This makes it extremely hard to put the
# separate pieces together in different places depending on what type of
# install we're doing.
#
# We can work around this by using package_data for static as eggs expect and
# then overriding install to install static in the correct place.
#
# Eventually someone needs to rewrite egg generation to tag files into
# separate groups (module, script, data, documentation, test) and put them
# into the final package format in the correct place.
#
# For some reason, the install-data switch also doesn't propogate to the build
# script.  So if we invoke install without --skip-build the app.cfg that is
# installed is also broken.  Grr....

class InstallData(_install_data, object):
    def finalize_options(self):
        '''Override to emulate setuptools in the default case.
        install_data => install_dir
        '''
        self.temp_lib = None
        self.temp_data = None
        self.temp_prefix = None
        haveInstallDir = self.install_dir
        self.set_undefined_options('install',
                ('install_data', 'temp_data'),
                ('install_lib', 'temp_lib'),
                ('prefix', 'temp_prefix'),
                ('root', 'root'),
                ('force', 'force'),
                )
        if not self.install_dir:
            if self.temp_data == self.root + self.temp_prefix:
                self.install_dir = os.path.join(self.temp_lib, 'fas')
            else:
                self.install_dir = self.temp_data

setup(
    name=NAME,
    version=VERSION,
    
    description=DESCRIPTION,
    author=AUTHOR,
    author_email=EMAIL,
    url=URL,
    download_url=DOWNLOAD_URL,
    license=LICENSE,
   
    cmdclass={
        'build': Build,
        'install_data': InstallData,
    },
    install_requires = [
        'TurboGears >= 1.0.4',
        'SQLAlchemy >= 0.4',
        'TurboMail',
        'python_fedora >= 0.2.99.2'
    ],
    scripts = ['client/fasClient', 'client/restricted-shell'],
    zip_safe=False,
    packages=find_packages(),
    data_files = (('static', [f for f in glob.glob('fas/static/*') if os.path.isfile(f)]),
        ('static/css', [f for f in glob.glob('fas/static/css/*') if os.path.isfile(f)]),
        ('static/images', [f for f in glob.glob('fas/static/images/*') if os.path.isfile(f)]),
        ('static/images/balloons',
            [f for f in glob.glob('fas/static/images/balloons/*') if os.path.isfile(f)]),
        ('static/js', [f for f in glob.glob('fas/static/js/*') if os.path.isfile(f)]),
        ('locales', [f for f in glob.glob('locales/*') if os.path.isfile(f)]),
        ('locales/xx/LC_MESSAGES', [f for f in glob.glob('locales/*/*/*') if os.path.isfile(f)]),
    ),
    package_data = find_package_data(where='fas',
        package='fas',
        exclude=excludeFiles,
        exclude_directories=excludeDataDirs,
    ),
    keywords = [
        # Use keywords if you'll be adding your package to the
        # Python Cheeseshop
        
        # if this has widgets, uncomment the next line
        # 'turbogears.widgets',
        
        # if this has a tg-admin command, uncomment the next line
        # 'turbogears.command',
        
        # if this has identity providers, uncomment the next line
        'turbogears.identity.provider',
    
        # If this is a template plugin, uncomment the next line
        # 'python.templating.engines',
        
        # If this is a full application, uncomment the next line
        'turbogears.app',
    ],
    classifiers = [
        'Development Status :: 4 - Beta',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Framework :: TurboGears',
        # if this is an application that you'll distribute through
        # the Cheeseshop, uncomment the next line
        'Framework :: TurboGears :: Applications',
        
        # if this is a package that includes widgets that you'll distribute
        # through the Cheeseshop, uncomment the next line
        # 'Framework :: TurboGears :: Widgets',
    ],
    test_suite = 'nose.collector',
    entry_points = {
            'console_scripts': (
                'start-fas = fas.commands:start',
            ),
            'turbogears.identity.provider': (
                'safas3 = fas.safasprovider:SaFasIdentityProvider',
            )
    }
)
