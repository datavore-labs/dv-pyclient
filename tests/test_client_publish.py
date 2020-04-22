#!/usr/bin/env python

'''test client.publish flows for uploading a data frame'''

import pytest
import copy
import numpy as np
import pandas as pd

import dv_pyclient.auth.auth as dv_auth
import dv_pyclient.client.publish as dv_client


@pytest.fixture
def session():
    '''Sample pytest fixture.

    See more at: http://doc.pytest.org/en/latest/fixture.html
    '''
    env_conf = {
        'authDomain': 'https://dev.datavorelabs.com/auth',
        'apiDomain': 'https://dev.datavorelabs.com/server',
        'execDomain': 'https://dev.datavorelabs.com/exec'
    }
    return dv_auth.login('dummy user', env_conf, 'dummy password')


@pytest.fixture
def data_frame():
    return pd.DataFrame({'A': 1.,
                         'B': pd.Timestamp('20130102'),
                         'C': pd.Series(1, index=list(range(4)), dtype='float32'),
                         'D': np.array([3] * 4, dtype='int32'),
                         'E': pd.Categorical(['test', 'train', 'test', 'train']),
                         'F': pd.Categorical(['a', 'a', 'b', 'a'])})


def test___get_pre_signed_url(session):
    data_source_id = '72c221ff-703e-11ea-9c7f-1fc811f9ee94'
    presigned_url = dv_client.__get_pre_signed_url(
        session, data_source_id)
    assert presigned_url.startswith(
        'http://dev-upload.datavorelabs.com:9000/dv-dev/dv-data-loader/uploads/'+data_source_id)


def test_set_data_loader_config(session):
    data_source_id = '72c221ff-703e-11ea-9c7f-1fc811f9ee94'
    empty_cfg = {
        'type': 'CsvDataLoaderConfig',
        'dataSource': {
            'docType': 'DataSource',
            'id': data_source_id,
        },
        'strategy': 'Overwrite',
        'loaderConfig': {
            'generated': True
        },
        'inputs': {}
    }
    resp = dv_client.set_data_loader_config(session, data_source_id, empty_cfg)
    assert resp.status_code == 200

def test_get_data_loader_config(session):
    data_source_id = '8eafff0a-7835-11ea-b299-55625c1ef477'
    configJson = dv_client.get_data_loader_config(session, data_source_id)
    assert configJson != None

def test_publish(session, data_frame):
    data_source_id = '72c221ff-703e-11ea-9c7f-1fc811f9ee94'
    resp = dv_client.publish(session, data_source_id, data_frame)
    assert resp.status_code == 200
