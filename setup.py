import os

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
    'pyramid_debugtoolbar',
    'zope.sqlalchemy',
    'waitress',
    'mako',
    'wtforms',
    'flufl.enum',
    'mistune',

    # Libs
    'GeoIP',
    'pygeoip',
    'ua-parser',
    'pyyaml',
    'cryptacular',
    'PyGithub',
    'PIL',
    'cryptography',

    # i18n
    'Babel',
    'lingua',

    # Test
    'fake-factory',
    ]

optional = {
    'rainbow': 'rainbow_logging_handler',
}

setup(
    name='fas',
    version='3.0',
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
    message_extractors = {'fas': [
            ('**.py', 'python', None),
            ('templates/**.xhtml', 'mako', None),
            ('static/**', 'ignore', None),
            ]},
    )
