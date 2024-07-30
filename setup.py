#!/usr/bin/env python

"""The setup script."""

from setuptools import setup, find_packages

with open('README.rst') as readme_file:
    readme = readme_file.read()

with open('HISTORY.rst') as history_file:
    history = history_file.read()

requirements = [
    "metloom>=0.4.0, <1.0",
    "utm",
    "numpy<2.0"
]

test_requirements = ['pytest>=3', ]

setup(
    author="M3 Works LLC",
    author_email='info@m3works.io',
    python_requires='>=3.6',
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
    ],
    description="Weave insitu data together",
    entry_points={
        'console_scripts': [
            'insitupy=insitupy.cli:main',
        ],
    },
    install_requires=requirements,
    license="MIT license",
    long_description=readme + '\n\n' + history,
    include_package_data=True,
    keywords='insitupy',
    name='insitupy',
    packages=find_packages(include=['insitupy', 'insitupy.*']),
    test_suite='tests',
    tests_require=test_requirements,
    url='https://github.com/m3works/insitupy',
    version='0.1.1',
    zip_safe=False,
)
