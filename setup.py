#!/usr/bin/env python

import os
import sys
from setuptools import setup, find_packages
from setuptools.command.test import test as TestCommand

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__),'RC522_Python')))

from RC522_Python import __version__
sys.path.pop(0)

setup(
    name='RC522-Python',
    packages=find_packages(),
    include_package_data=True,
    version=__version__,
    download_url = 'https://github.com/STEMinds/RC522-Python/archive/1.0.0.tar.gz',
    keywords = ['python', 'raspberry-pi', 'RC522', 'RFID', 'NFC', 'SPI'],
    description='Raspberry Pi Python library for SPI RFID RC522 module.',
    long_description='Raspberry Pi Python library for SPI RFID RC522 module.',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GNU Affero General Public License v3 or later (AGPLv3+)',
        'Operating System :: OS Independent',
        'Topic :: Software Development',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
    ],
    author='STEMinds',
    author_email='contact@steminds.com',
    url='https://github.com/STEMinds/RC522-Python',
    license='GNU Lesser General Public License v3.0',
    install_requires=['SPI-Py', 'RPi.GPIO'],
)
