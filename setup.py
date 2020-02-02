#!/usr/bin/env python

"""The setup script."""

from setuptools import setup, find_packages

with open('README.rst') as readme_file:
    readme = readme_file.read()

with open('HISTORY.rst') as history_file:
    history = history_file.read()

requirements = ['Click>=7.0', 'ndjson==0.2.0', 'requests==2.22.0', 'pandas==1.0.0', 'numpy==1.18.1', 'jwt=0.6.1',
                'PyJWT']

setup_requirements = [ ]

test_requirements = [ ]

setup(
    author="Datavore Labs",
    author_email='info@datavorelabs.com',
    python_requires='>=3.5',
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
    ],
    description="Datavore python client to connect to API server",
    entry_points={
        'console_scripts': [
            'dv_pyclient=dv_pyclient.cli:main',
        ],
    },
    install_requires=requirements,
    license="MIT license",
    long_description=readme + '\n\n' + history,
    include_package_data=True,
    keywords='dv_pyclient',
    name='dv_pyclient',
    packages=find_packages(include=['dv_pyclient', 'dv_pyclient.*']),
    setup_requires=setup_requirements,
    test_suite='tests',
    tests_require=test_requirements,
    url='https://github.com/sanjayvenkat2000/dv_pyclient',
    version='0.1.7',
    zip_safe=False,
)
