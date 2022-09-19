#!/usr/bin/env python

import os
import sys
from setuptools import setup, find_packages

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'rpi_rc522')))

from rpi_rc522 import __version__

sys.path.pop(0)

setup(
    name='RPi-RFIDReader',
    packages=find_packages(),
    include_package_data=True,
    version=__version__,
    download_url='https://github.com/Mik3Rizzo/rpi-rc522/archive/refs/tags/v1.0.0-beta.tar.gz',
    keywords=['python', 'raspberry-pi', 'RFIDReader', 'RFID', 'NFC', 'SPI'],
    description='Raspberry Pi python library for SPI RFID RFIDReader module.',
    long_description='Raspberry Pi Python library for SPI RFID RFIDReader module.',
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
        'Programming Language :: Python :: 3.10',
    ],
    author='Michele Rizzo',
    author_email='m.rizzo006@studenti.unibs.it',
    url='https://github.com/Mik3Rizzo/rpi-rc522',
    license='GNU Lesser General Public License v3.0',
    install_requires=['SPI-Py', 'RPi.GPIO'],
)
