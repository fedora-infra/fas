#!/usr/bin/python -tt

import os

from setuptools import setup, find_packages
from turbogears.finddata import find_package_data

execfile(os.path.join('fas', 'release.py'))

setup(
    name=NAME,
    version=VERSION,
    
    description=DESCRIPTION,
    author=AUTHOR,
    author_email=EMAIL,
    url=URL,
    download_url=DOWNLOAD_URL,
    license=LICENSE,
   
    #cmdclass={'build_scripts': BuildScripts,
    #          'build': Build,
    #          'install': Install,
    #          'install_lib': InstallApp},
    install_requires = [
        'TurboGears >= 1.0.4',
        'SQLAlchemy >= 0.4',
        'TurboMail',
        'python_fedora >= 0.2.99.2'
    ],
    scripts = ['client/fasClient.py'],
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
    
