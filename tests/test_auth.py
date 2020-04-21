#!/usr/bin/env python

'''Testing auth flows'''

import pytest

from dv_pyclient.auth import auth

def test_auth_login_no_env_conf_throw():
    with pytest.raises(Exception) as e_info:
        auth.login()
    assert 'Invalid env_conf' in str(e_info)
