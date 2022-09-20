#!/usr/bin/env python

import os
import sys
from setuptools import setup, find_packages

#sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'rpi_rc522')))

from rpi_rc522 import __version__

#sys.path.pop(0)

setup(
    name='rpi-rc522',
    version=__version__,
    packages=find_packages(),
    include_package_data=True,
    download_url='https://github.com/Mik3Rizzo/rpi-rc522/archive/refs/tags/v1.0.0-beta.tar.gz',
    keywords=['RC522', 'python', 'Raspberry Pi', 'RFID', 'NFC', 'SPI'],
    description='Raspberry Pi python3 library for SPI RFID RC522 module.',
    classifiers=[
        'Development Status :: Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GNU Affero General Public License v3 or later (AGPLv3+)',
        'Operating System :: OS Independent',
        'Topic :: Software Development',
        'Programming Language :: Python :: 3',
    ],
    author='Michele Rizzo',
    author_email='m.rizzo006@studenti.unibs.it',
    url='https://github.com/Mik3Rizzo/rpi-rc522',
    license='GNU Lesser General Public License v3.0',
    install_requires=['SPI-Py', 'RPi.GPIO'],
)
