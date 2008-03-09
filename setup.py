#!/usr/bin/python -tt

import os
import re

from distutils.command.build import build as _build
from distutils.dep_util import newer

from setuptools import setup, find_packages
from turbogears.finddata import find_package_data

execfile(os.path.join('fas', 'release.py'))

SUBSTFILES=('fas/config/app.cfg',)

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
        #'build_scripts': BuildScripts,
    #          'install': Install,
    #          'install_lib': InstallApp},
    },
    install_requires = [
        'TurboGears >= 1.0.4',
        'SQLAlchemy >= 0.4',
        'TurboMail',
        'python_fedora >= 0.2.99.2'
    ],
    scripts = ['client/fasClient.py', 'client/restricted-shell'],
    zip_safe=False,
    packages=find_packages(),
    package_data = find_package_data(where='fas',
                                     package='fas'),
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
    
