#!/usr/bin/env python3

from setuptools import setup

VERSION = '0.1'

setup(
    name='prometheus-data-generator',
    version=VERSION,
    description='',
    license="GPLv3",
    install_requires=["flask", "prometheus_client", "pyyaml"],
)
