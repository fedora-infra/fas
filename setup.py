import os

from setuptools import setup, find_packages

here = os.path.abspath(os.path.dirname(__file__))
README = open(os.path.join(here, 'README.rst')).read()
CHANGES = open(os.path.join(here, 'CHANGES.txt')).read()

requires = [
    'pyramid',
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

    #i18n
    'Babel',
    'lingua',

    #Test
    'fake-factory',
    ]

setup(name='fas',
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
      keywords='fedora fedoraproject web wsgi pyramid',
      packages=find_packages(),
      include_package_data=True,
      zip_safe=False,
      test_suite='fas',
      install_requires=requires,
      entry_points="""\
      [paste.app_factory]
      main = fas:main
      [console_scripts]
      initialize_fas_db = fas.scripts.initializedb:main
      """,
      paster_plugins=['pyramid'],
      )
