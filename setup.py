"""

##################################################################################
Copyright 2022 Jean-Francois Auger <jeanfrancois.auger@spie.com>

    This file is part of lora-survey-heatmap, also known as lora-survey-heatmap.

    lora-survey-heatmap is free software: you can redistribute it and/or modify
    it under the terms of the GNU Affero General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    lora-survey-heatmap is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU Affero General Public License for more details.

    You should have received a copy of the GNU Affero General Public License
    along with lora-survey-heatmap.  If not, see <http://www.gnu.org/licenses/>.

The Copyright and Authors attributions contained herein may not be removed or
otherwise altered, except to add the Author attribution of a contributor to
this work. (Additional Terms pursuant to Section 7b of the AGPL v3)
##################################################################################
While not legally required, I sincerely request that anyone who finds
bugs please submit them at <https://github.com/nechry/lora-survey-heatmap> or
to me via email, and that you send any contributions or improvements
either as a pull request on GitHub, or to me via email.
##################################################################################

AUTHORS:
Jean-Francois Auger <jeanfrancois.auger@spie.com> <http://spie.ch>
##################################################################################
"""

from setuptools import setup, find_packages

# read the contents of your README file
from pathlib import Path
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text()

requires = [
    'matplotlib==3.3.0',
    'scipy==1.5.2',
    'libnl3==0.3.0',
]

classifiers = [
    'Development Status :: 1 - Planning',
    'Environment :: X11 Applications :: GTK',
    'Intended Audience :: End Users/Desktop',
    'Intended Audience :: Information Technology',
    'Intended Audience :: System Administrators',
    'License :: OSI Approved :: GNU Affero General Public License '
    'v3 or later (AGPLv3+)',
    'Natural Language :: English',
    'Operating System :: POSIX :: Linux',
    'Programming Language :: Python',
    'Programming Language :: Python :: 3',
    'Programming Language :: Python :: 3.4',
    'Programming Language :: Python :: 3.5',
    'Programming Language :: Python :: 3.6',
    'Programming Language :: Python :: 3.7',
    'Programming Language :: Python :: 3.8',
    'Programming Language :: Python :: 3.9',
    'Programming Language :: Python :: 3.10',
    'Topic :: System :: Networking'
]

setup(
    name='lora_survey_heatmap',
    version='1.0.0',
    author='Jean-Francois Auger',
    author_email='nechry@gmail.com',
    packages=find_packages(),
    url='',
    description='A Python application to display LoRa survey data in a heatmap.',
    long_description=long_description,
    install_requires=requires,
    setup_requires=['cffi>=1.0.0'],
    keywords="lora survey rssi heatmap",
    classifiers=classifiers,
    entry_points={
        'console_scripts': [
            'lora-heatmap = lora_survey_heatmap.heatmap:main',
            'lora-heatmap-thresholds = lora_survey_heatmap.thresholds:main'
        ]
    },
    zip_safe=False
)
