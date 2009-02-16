# Asterisk Plugin for FAS2
__requires__='TurboGears >= 1.0.4'

from setuptools import setup, find_packages
from turbogears.finddata import find_package_data, standard_exclude, \
        standard_exclude_directories
import os, glob

excludeFiles = []
excludeFiles.extend(standard_exclude)
excludeDataDirs = []
excludeDataDirs.extend(standard_exclude_directories)

package_data = find_package_data(where='fas_asterisk', package='fas_asterisk', exclude=excludeFiles, exclude_directories=excludeDataDirs,)

setup(
    name = "fas-plugin-asterisk",
    version = "0.6",
    packages = find_packages(),

    package_data = package_data,
        
    author = "Mike McGrath",
    author_email = "mmcgrath@redhat.com",
    description = "Asterisk plugin for FAS2",
    entry_points = {
            'fas.plugins': (
                'Asterisk = fas_asterisk:AsteriskPlugin',
            )
    }
)
