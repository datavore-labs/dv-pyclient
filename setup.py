#!/usr/bin/env python

"""The setup script."""

from setuptools import setup, find_packages

requirements = ['Click>=7.0', 'pandas', 'numpy', 'PyJWT', 'requests', 'ndjson', 'grpcio>=1.27.2', 'protobuf']

setup_requirements = ['pytest-runner', ]

test_requirements = ['pytest>=3', ]

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
    description="Python client for datavore. Connection auth and grpc support",
    entry_points={
        'console_scripts': [
            'dv_pyclient=dv_pyclient.cli:main',
        ],
    },
    install_requires=requirements,
    license="MIT license",
    long_description="dv_pyclient package for client and grpc services",
    include_package_data=True,
    keywords='dv_pyclient',
    name='dv_pyclient',
    packages=find_packages(include=['dv_pyclient', 'dv_pyclient.*']),
    setup_requires=setup_requirements,
    test_suite='tests',
    tests_require=test_requirements,
    url='https://github.com/datavore-labs/dv-pyclient',
    version='0.5.0',
    zip_safe=False,
)
