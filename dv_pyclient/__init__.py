"""Top-level package for Datavore Python Client."""

__author__ = """Datavore Labs"""
__email__ = 'info@datavorelabs.com'
__version__ = '0.1.7'

from .dv_pyclient import _login, _get_data


def login(user_name, password, env_conf):
    return login(user_name, password, env_conf)


def get_data(session, data_conf):
    return _get_data(session, data_conf)
