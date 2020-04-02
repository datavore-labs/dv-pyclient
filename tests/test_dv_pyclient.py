#!/usr/bin/env python

"""Tests for `dv_pyclient` package."""

import pytest
import numpy as np
import pandas as pd

from click.testing import CliRunner

from dv_pyclient import dv_pyclient
from dv_pyclient import cli


@pytest.fixture
def session():
    """Sample pytest fixture.

    See more at: http://doc.pytest.org/en/latest/fixture.html
    """
    password = "dummy password"
    env_conf = {
        'authDomain': 'https://dev.datavorelabs.com/auth',
        'apiDomain': 'https://dev.datavorelabs.com'
    }
    return dv_pyclient.login("JP Kosmyna", env_conf, password)


@pytest.fixture
def dataFrame():
    return pd.DataFrame({'A': 1.,
                         'B': pd.Timestamp('20130102'),
                         'C': pd.Series(1, index=list(range(4)), dtype='float32'),
                         'D': np.array([3] * 4, dtype='int32'),
                         'E': pd.Categorical(["test", "train", "test", "train"]),
                         'F': 'foo'})


def test___generateDataSourceLoaderConfig(dataFrame):
    result = dv_pyclient.__generateDataSourceLoaderConfig(
        dataFrame, "userName", "dataSourceid", None, [], [])
    print(result)
    assert True


def test___getPreSignedUrl(session):
    dataSourceId = "72c221ff-703e-11ea-9c7f-1fc811f9ee94"
    presignedUrl = dv_pyclient.__getPreSignedUrl(
        session, dataSourceId)
    assert presignedUrl.startswith(
        "http://dev-upload.datavorelabs.com:9000/dv-dev/dv-data-loader/uploads/"+dataSourceId)


def test__setDataSourceLoaderConfig(session):
    dataSourceId = "72c221ff-703e-11ea-9c7f-1fc811f9ee94"
    emptyLoaderConfig = {
        'type': 'CsvDataLoaderConfig',
        'dataSource': {
            'docType': 'DataSource',
            'id': dataSourceId,
        },
        'strategy': 'Overwrite',
        'loaderConfig': {},
        'inputs': {}
    }
    resp = dv_pyclient.__setDatasourceLoaderConfig(
        session, dataSourceId, emptyLoaderConfig)
    assert resp.status_code == 200

def test__validateLoaderConfig_empty():
    # No config
    with pytest.raises(Exception) as e_info:
        dv_pyclient.__validateLoaderConfig({})
        assert str(e_info) == "Empty loader config"

def test__validateLoaderConfig_noTime():
    # No time columns
    with pytest.raises(Exception) as e_info:
        df = pd.DataFrame({})
        dv_pyclient.__validateLoaderConfig(
            dv_pyclient.__generateDataSourceLoaderConfig(df, "", "", None, [], [])
        )
        assert str(e_info) == "Loader config requires non-empty time columns."

def test__validateLoaderConfig_noTuples():
    # No time columns
    with pytest.raises(Exception) as e_info:
        df = pd.DataFrame({
            'Date': pd.Timestamp('20130102')
        })
        dv_pyclient.__validateLoaderConfig(
            dv_pyclient.__generateDataSourceLoaderConfig(df, "", "", None, [], [])
        )
        assert str(e_info) == "Time tuples empty. No column loaded."

def test__validateLoaderConfig_valid():
    # No time columns
    df = pd.DataFrame({
        'Date': pd.Timestamp('20130102'),
        'Value': pd.Series(1, index=list(range(4)), dtype='float32')
    })
    assert dv_pyclient.__validateLoaderConfig(
        dv_pyclient.__generateDataSourceLoaderConfig(df, "", "", None, [], [])
    )

def test_publish(session, dataFrame):
    dataSourceId = "72c221ff-703e-11ea-9c7f-1fc811f9ee94"
    resp = dv_pyclient.publish(session, dataSourceId, dataFrame)
    assert resp.status_code == 200


def test_command_line_interface():
    """Test the CLI."""
    runner = CliRunner()
    result = runner.invoke(cli.main)
    assert result.exit_code == 0
    assert 'dv_pyclient.cli.main' in result.output
    help_result = runner.invoke(cli.main, ['--help'])
    assert help_result.exit_code == 0
    assert '--help  Show this message and exit.' in help_result.output
