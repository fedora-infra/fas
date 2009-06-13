#!/usr/bin/python -tt
__requires__='TurboGears >= 1.0.4'
import os
import re
import glob
import subprocess
import shutil

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

poFiles = filter(os.path.isfile, glob.glob('po/*.po'))

SUBSTFILES = ('fas/config/app.cfg',)

class Build(_build, object):
    '''
    Build the package, changing the directories that data files are installed.
    '''
    user_options = _build.user_options
    user_options.extend([('install-data=', None,
        'Installation directory for data files')])
    # These are set in finalize_options()
    substitutions = {'@DATADIR@': None, '@LOCALEDIR@': None}
    subRE = re.compile('(' + '|'.join(substitutions.keys()) + ')+')

    def initialize_options(self):
        self.install_data = None
        super(Build, self).initialize_options()

    def finalize_options(self):
        if self.install_data:
            self.substitutions['@DATADIR@'] = self.install_data + '/fas'
            self.substitutions['@LOCALEDIR@'] = self.install_data + '/locale'
        else:
            self.substitutions['@DATADIR@'] = '%(top_level_dir)s'
            self.substitutions['@LOCALEDIR@'] = '%(top_level_dir)s/../locale'
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

        # Make empty en.po
        dirname = 'locale/'
        if not os.path.isdir(dirname):
            os.makedirs(dirname)
        shutil.copy('po/LINGUAS', 'locale/')

        for pofile in poFiles:
            # Compile PO files
            lang = os.path.basename(pofile).rsplit('.', 1)[0]
            dirname = 'locale/%s/LC_MESSAGES/' % lang
            if not os.path.isdir(dirname):
                os.makedirs(dirname)
            # Hardcoded gettext domain: 'fas'
            mofile = dirname + 'fas' + '.mo'
            subprocess.call(['/usr/bin/msgfmt', pofile, '-o', mofile])
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

# fas/static => /usr/share/fas/static
data_files = [('fas/static', filter(os.path.isfile, glob.glob('fas/static/*'))),
    ('fas/static/css', filter(os.path.isfile, glob.glob('fas/static/css/*'))),
    ('fas/static/images', filter(os.path.isfile, glob.glob('fas/static/images/*'))),
    ('fas/static/images/balloons', filter(os.path.isfile, glob.glob('fas/static/images/balloons/*'))),
    ('fas/static/js', filter(os.path.isfile, glob.glob('fas/static/js/*'))),
    ('fas/static/theme', filter(os.path.isfile, glob.glob('fas/static/theme/*'))),
    ('fas/static/theme/fas', filter(os.path.isfile, glob.glob('fas/static/theme/fas/*'))),
    ('fas/static/theme/fas/css', filter(os.path.isfile, glob.glob('fas/static/theme/fas/css/*'))),
    ('fas/static/theme/fas/images', filter(os.path.isfile, glob.glob('fas/static/theme/fas/images/*'))),
]
for langfile in filter(os.path.isfile, glob.glob('locale/*/*/*')):
    data_files.append((os.path.dirname(langfile), [langfile]))

package_data = find_package_data(where='fas', package='fas', exclude=excludeFiles, exclude_directories=excludeDataDirs,)
# Even if it doesn't exist yet, has to be in the list to be included in the build.
package_data['fas.config'].append('app.cfg')

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
        'python_fedora >= 0.3'
    ],
    scripts = [
        'client/fasClient',
        'client/fasClient.old',
        'client/restricted-shell',
        'scripts/account-expiry.py',
        'scripts/export-bugzilla.py',
    ],
    zip_safe=False,
    packages=find_packages(),
    data_files = data_files,
    package_data = package_data,
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
                'safas4 = fas.safasprovider:SaFasIdentityProvider',
            ),
    }
)
