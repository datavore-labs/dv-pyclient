"""Top-level package for Datavore Python Client."""

__author__ = """Datavore Labs"""
__email__ = 'info@datavorelabs.com'
__version__ = '0.1.5'

from . import dv_pyclient


def hello():
    dv_pyclient.hello()
