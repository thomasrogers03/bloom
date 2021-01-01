# Copyright 2020 Thomas Rogers
# SPDX-License-Identifier: Apache-2.0

import os.path

import setuptools


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


def _get_version():
    directory = os.path.dirname(__file__)
    version_path = os.path.join(directory, 'version.txt')

    with open(version_path, 'r') as file:
        return file.readlines()[0].strip()


native_module = setuptools.Extension(
    'bloom.native.loader.walls',
    sources=['bloom/native/loader/wallsmodule.cpp'],
)

setuptools.setup(
    name="bloom",
    version=_get_version(),
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
    include_package_data=True,
    python_requires='>=3.6',
    install_requires=_install_requires(),
    options={
        'build_apps': {
            'include_patterns': [
                'bloom/resources/*.*',
                'bloom/pre_cache/*.*',
                'bloom/examples/*.*',
                'README.url',
            ],
            'console_apps': {'bloom': 'run_bloom.py'},
            'plugins': [
                'pandagl',
                'p3tinydisplay',
                'pandadx9',
                'p3openal_audio',
            ],
            'platforms': ['win_amd64']
        }
    },
    ext_modules=[native_module]
)
