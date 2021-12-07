#!/usr/bin/env python3

import pathlib
from setuptools import setup

HERE = pathlib.Path(__file__).parent
README = (HERE / 'README.md').read_text()

NAME = 'refery'
VERSION = '1.0.1'
DESCRIPTION = 'Functional testing tool'
AUTHOR = 'Rostan Tabet'
EMAIL = 'rostan.tabet@gmail.com'
REQUIRED = ['PyYAML', 'colorama']

setup(
    name=NAME,
    version=VERSION,
    description=DESCRIPTION,
    author=AUTHOR,
    author_email=EMAIL,
    packages=['src'],
    install_requires=REQUIRED,
    long_description_content_type='text/markdown',
    long_description=README,
    entry_points={
        'console_scripts': [
            'refery=src.main:main'
        ]
    }
)
