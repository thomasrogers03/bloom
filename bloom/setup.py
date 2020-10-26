# Copyright 2020 Thomas Rogers
# SPDX-License-Identifier: Apache-2.0

import setuptools
import os.path


def _install_requires():
    directory = os.path.dirname(__file__)
    with open(os.path.join(directory, 'requirements.txt'), 'r') as file:
        lines = [
            line
            for line in file.readlines()
            if not line.startswith('#') and len(line.strip()) > 0
        ]


setuptools.setup(
    name="bloom",
    version="0.0.1",
    author="Thomas Rogers",
    author_email="thomasrogers03@gmail.com",
    description="Blood Modding Suite",
    url="https://github.com/thomasrogers03/bloom",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: Apache-2.0",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
    install_requires=_install_requires(),
    entry_points={"console_scripts": ["bloom=bloom.__main__:main"]}
)
