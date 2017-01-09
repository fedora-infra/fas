import os

execfile(os.path.join('fas', 'release.py'))

from setuptools import setup, find_packages

here = os.path.abspath(os.path.dirname(__file__))
README = open(os.path.join(here, 'README.rst')).read()
CHANGES = open(os.path.join(here, 'CHANGES.txt')).read()

requires = [
    # Core
    'pyramid>=1.5.1',
    'pyramid_mako',
    'SQLAlchemy',
    'transaction',
    'pyramid_tm',
    'zope.sqlalchemy',
    'waitress',
    'mako',
    'wtforms',
    'mistune',

    # Libs
    'GeoIP',
    'pygeoip',
    'ua-parser',
    'pyyaml',
    'PyGithub',
    'pillow',
    'cryptography',
    'fedmsg',

    # i18n
    'Babel',
    'lingua',
]

optional = {
    'debug': 'pyramid_debugtoolbar',
    'fancy_log': 'rainbow_logging_handler',
    'db_upgrade': 'alembic',
    'fake-data': 'Faker',
}

setup(
    name='fas',
    version=__VERSION__,
    description='Fedora Account System',
    long_description=README + '\n\n' + CHANGES,
    classifiers=[
        "Programming Language :: Python",
        "Framework :: Pyramid",
        "Topic :: Internet :: WWW/HTTP",
        "Topic :: Internet :: WWW/HTTP :: WSGI :: Application",
    ],
    author='Xavier Lamien',
    author_email='laxathom@fedoraproject.org',
    url='',
    keywords='fedora,fedoraproject,web,wsgi,pyramid',
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
    test_suite='fas',
    install_requires=requires,
    extras_require=optional,
    entry_points="""\
      [paste.app_factory]
      main = fas:main
      [console_scripts]
      fas-admin = fas.scripts.admin:main
      """,
    paster_plugins=['pyramid'],
    # i18n
    message_extractors=dict(fas=[
        ('**.py', 'python', None),
        ('templates/**.xhtml', 'mako', None),
        ('static/**', 'ignore', None),
    ]),
)
