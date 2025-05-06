#!/usr/bin/env python
"""
Setup for the openedx_pok Django app.
"""

import os
import re
import sys
from setuptools import find_packages, setup


def is_requirement(line):
    """
    Return True if the line is a valid requirement (not a comment or constraint).
    """
    return line and line.strip() and not line.startswith(('-r', '#', '-e', 'git+', '-c'))


def load_requirements(*requirements_paths):
    """
    Load all requirements from specified requirements files.
    Supports `-c constraints.txt`.
    """
    requirements = {}
    constraint_files = set()
    by_canonical_name = {}

    def check_name_consistent(package):
        canonical = package.lower().replace('_', '-').split('[')[0]
        seen = by_canonical_name.get(canonical)
        if seen and seen != package:
            raise Exception(
                f'Inconsistent naming: "{seen}" and "{package}". Use one consistent name.'
            )
        by_canonical_name[canonical] = package

    requirement_line_regex = re.compile(
        r"([a-zA-Z0-9\-_\.]+(?:\[[a-zA-Z0-9,\s\-_\.]+\])?)([<>=][^#\s]+)?"
    )

    def add_line(line, add_if_not_present):
        match = requirement_line_regex.match(line)
        if match:
            package, constraint = match.groups()
            check_name_consistent(package)
            existing = requirements.get(package)
            if existing and existing != constraint:
                raise Exception(
                    f'Conflicting constraints for {package}: {existing} vs {constraint}'
                )
            if add_if_not_present or package in requirements:
                requirements[package] = constraint

    for path in requirements_paths:
        if not os.path.exists(path):  # Manejar archivos inexistentes
            print(f"Warning: Requirements file {path} not found. Skipping.")
            continue
        with open(path) as f:
            for line in f:
                if is_requirement(line):
                    add_line(line, add_if_not_present=True)
                elif line.strip().startswith('-c'):
                    constraint_file = line.split('#')[0].replace('-c', '').strip()
                    constraint_files.add(os.path.join(os.path.dirname(path), constraint_file))

    for constraint_file in constraint_files:
        if not os.path.exists(constraint_file):  # Manejar archivos inexistentes
            print(f"Warning: Constraint file {constraint_file} not found. Skipping.")
            continue
        with open(constraint_file) as f:
            for line in f:
                if is_requirement(line):
                    add_line(line, add_if_not_present=False)

    return [f'{pkg}{ver or ""}' for pkg, ver in sorted(requirements.items())]


def get_version(*file_paths):
    """
    Extract the __version__ string from a file.
    """
    path = os.path.join(os.path.dirname(__file__), *file_paths)
    with open(path, encoding='utf-8') as f:
        version_file = f.read()
    match = re.search(r"^__version__ = ['\"]([^'\"]+)['\"]", version_file, re.M)
    if match:
        return match.group(1)
    raise RuntimeError('Unable to find version string.')


VERSION = get_version('openedx_pok', '__init__.py')

if sys.argv[-1] == 'tag':
    print(f"Tagging version {VERSION} on GitHub:")
    os.system(f"git tag -a {VERSION} -m 'version {VERSION}'")
    os.system("git push --tags")
    sys.exit()

with open('README.rst', encoding='utf-8') as f:
    README = f.read()
with open('CHANGELOG.rst', encoding='utf-8') as f:
    CHANGELOG = f.read()

setup(
    name='openedx-pok',
    version=VERSION,
    author='aulasneo',
    author_email='lberoes@aulasneo.com',
    description='POK integration module for Open edX platform.',
    long_description=README + '\n\n' + CHANGELOG,
    long_description_content_type='text/x-rst',
    url='https://github.com/openedx/openedx-pok',
    license='AGPL',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Framework :: Django',
        'Framework :: Django :: 4.2',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: 3.12',
        'License :: OSI Approved :: GNU Affero General Public License v3',
        'Intended Audience :: Developers',
        'Operating System :: OS Independent',
    ],
    packages=find_packages(
        include=['openedx_pok', 'openedx_pok.*'],
        exclude=['*.tests', '*.test'],
    ),
    package_data={
        'openedx_pok': ['test_settings.py'],  # Asegúrate de incluir test_settings.py
    },
    include_package_data=True,
    install_requires=load_requirements('requirements/base.in'),
    tests_require=load_requirements('requirements/test.in'),
    python_requires='>=3.11',
    entry_points={
        'lms.djangoapp': [
            'openedx_pok = openedx_pok.apps:OpenedxPokConfig',
        ],
        'cms.djangoapp': [
            'openedx_pok = openedx_pok.apps:OpenedxPokConfig',
        ],
    },
    zip_safe=False,
    keywords='Open edX, webhook, integration, POK, LMS',
)
