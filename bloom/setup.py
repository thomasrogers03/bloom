# Copyright 2020 Thomas Rogers
# SPDX-License-Identifier: Apache-2.0

import setuptools
import os.path


def _install_requires():
    directory = os.path.dirname(__file__)
    requirements_path = os.path.join(directory, 'requirements.txt')
    
    with open(requirements_path, 'r') as file:
        lines = [
            line.strip()
            for line in file.readlines()
            if not line.startswith('#') and len(line.strip()) > 0
        ]
    return lines

setuptools.setup(
    name="bloom",
    version="0.0.4",
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
    options={
        'build_apps': {
            'include_patterns': [
                '**/*.png',
                '**/*.jpg',
                '**/*.egg',
            ],
            'gui_apps': {'bloom': 'run_bloom.py'},
            'plugins': [
                'pandagl',
                'p3tinydisplay',
                'pandadx9',
                'p3openal_audio',
            ],
            'platforms': ['win_amd64']
        }
    }
)
