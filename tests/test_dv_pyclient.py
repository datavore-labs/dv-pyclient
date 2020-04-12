#!/usr/bin/env python

'''Tests for `dv_pyclient` package.'''

import pytest
import copy
import numpy as np
import pandas as pd

from click.testing import CliRunner

from dv_pyclient import dv_pyclient
from dv_pyclient import cli


@pytest.fixture
def session():
    '''Sample pytest fixture.

    See more at: http://doc.pytest.org/en/latest/fixture.html
    '''
    password = 'dummy password'
    env_conf = {
        'authDomain': 'https://dev.datavorelabs.com/auth',
        'apiDomain': 'https://dev.datavorelabs.com/server',
        'execDomain': 'https://dev.datavorelabs.com/exec'
    }
    return dv_pyclient.login('JP Kosmyna', env_conf, password)


@pytest.fixture
def dataFrame():
    return pd.DataFrame({'A': 1.,
                         'B': pd.Timestamp('20130102'),
                         'C': pd.Series(1, index=list(range(4)), dtype='float32'),
                         'D': np.array([3] * 4, dtype='int32'),
                         'E': pd.Categorical(['test', 'train', 'test', 'train']),
                         'F': pd.Categorical(['a', 'a', 'b', 'a'])})


def test___generateDataSourceLoaderConfig(dataFrame):
    result = dv_pyclient.__generateDataSourceLoaderConfig(
        dataFrame, 'userName', 'dataSourceid', None, [], [])
    print(result)
    assert True


def test___getPreSignedUrl(session):
    dataSourceId = '72c221ff-703e-11ea-9c7f-1fc811f9ee94'
    presignedUrl = dv_pyclient.__getPreSignedUrl(
        session, dataSourceId)
    assert presignedUrl.startswith(
        'http://dev-upload.datavorelabs.com:9000/dv-dev/dv-data-loader/uploads/'+dataSourceId)


def test__setDataSourceLoaderConfig(session):
    dataSourceId = '72c221ff-703e-11ea-9c7f-1fc811f9ee94'
    emptyLoaderConfig = {
        'type': 'CsvDataLoaderConfig',
        'dataSource': {
            'docType': 'DataSource',
            'id': dataSourceId,
        },
        'strategy': 'Overwrite',
        'loaderConfig': {
            'generated': True
        },
        'inputs': {}
    }
    resp = dv_pyclient.__setDatasourceLoaderConfig(
        session, dataSourceId, emptyLoaderConfig)
    assert resp.status_code == 200

def test__getDatasourceLoaderConfig(session):
    dataSourceId = '8eafff0a-7835-11ea-b299-55625c1ef477'
    configJson = dv_pyclient.__getDatasourceLoaderConfig(session, dataSourceId)
    # print(configJson)
    assert configJson != None


def test__validateLoaderConfig_empty():
    # No config
    with pytest.raises(Exception) as e_info:
        dv_pyclient.__validateLoaderConfig({})
    assert 'Empty loader config' in str(e_info)


def test__validateLoaderConfig_noTime():
    # No time columns
    with pytest.raises(Exception) as e_info:
        df = pd.DataFrame({})
        dv_pyclient.__validateLoaderConfig(
            dv_pyclient.__generateDataSourceLoaderConfig(
                df, '', '', None, [], [])
        )
    assert 'Loader config requires non-empty time columns.' in str(e_info)


def test__validateLoaderConfig_noTuples():
    # No time/value tuples
    with pytest.raises(Exception) as e_info:
        df = pd.DataFrame({
            'String': pd.Categorical(['a', 'a', 'b', 'a']),
            'Date': pd.Timestamp('20130102')
        })
        dv_pyclient.__validateLoaderConfig(
            dv_pyclient.__generateDataSourceLoaderConfig(
                df, '', '', None, [], [])
        )
    assert 'Time tuples empty. No column loaded.' in str(e_info)


def test__validateLoaderConfig_configTypeCheck():
    df = pd.DataFrame({
        'String': pd.Categorical(['a', 'a', 'b', 'a']),
        'Date': pd.Timestamp('20130102'),
        'Value': np.array([3] * 4, dtype='int32')
    })
    baseConfig = dv_pyclient.__generateDataSourceLoaderConfig(df, '', '', None, [], [])

    # all keyColumns defined
    with pytest.raises(Exception) as e_info:
        local = copy.deepcopy(baseConfig)
        local['loaderConfig']['mapping']['keyColumns'] = ['NotAField']
        dv_pyclient.__validateLoaderConfig(local)
    assert 'key column NotAField not found' in str(e_info)

    # all keyColumns are strings
    with pytest.raises(Exception) as e_info:
        local = copy.deepcopy(baseConfig)
        local['loaderConfig']['mapping']['keyColumns'] = ['Date']
        dv_pyclient.__validateLoaderConfig(local)
    assert 'key column Date must be a string' in str(e_info)

    # all valueLabelColumn are defined
    with pytest.raises(Exception) as e_info:
        local = copy.deepcopy(baseConfig)
        local['loaderConfig']['mapping']['valueLabelColumn'] = ['NotAField']
        dv_pyclient.__validateLoaderConfig(local)
    assert 'value label NotAField not found' in str(e_info)

    # all valueLabelColumn are strings
    with pytest.raises(Exception) as e_info:
        local = copy.deepcopy(baseConfig)
        local['loaderConfig']['mapping']['valueLabelColumn'] = ['Date']
        dv_pyclient.__validateLoaderConfig(local)
    assert 'value label Date must be a string' in str(e_info)

    # all timeColumns are defined
    with pytest.raises(Exception) as e_info:
        local = copy.deepcopy(baseConfig)
        local['loaderConfig']['mapping']['timeColumns'] = ['NotAField']
        dv_pyclient.__validateLoaderConfig(local)
    assert 'time column NotAField not found' in str(e_info)

    # all timeColumns are time
    with pytest.raises(Exception) as e_info:
        local = copy.deepcopy(baseConfig)
        local['loaderConfig']['mapping']['timeColumns'] = ['String']
        dv_pyclient.__validateLoaderConfig(local)
    assert 'time column String must be a time' in str(e_info)

    # all timeTuples times are defined
    with pytest.raises(Exception) as e_info:
        local = copy.deepcopy(baseConfig)
        local['loaderConfig']['mapping']['timeTuples'][0]['timeColumn'] = 'NotAField'
        dv_pyclient.__validateLoaderConfig(local)
    assert 'not found' in str(e_info)

    # all timeTuples times are time
    with pytest.raises(Exception) as e_info:
        local = copy.deepcopy(baseConfig)
        local['loaderConfig']['mapping']['timeTuples'][0]['timeColumn'] = 'String'
        dv_pyclient.__validateLoaderConfig(local)
    assert 'must be a time' in str(e_info)

    # all timeTuples values are defined
    with pytest.raises(Exception) as e_info:
        local = copy.deepcopy(baseConfig)
        local['loaderConfig']['mapping']['timeTuples'][0]['valueColumn'] = 'NotAField'
        dv_pyclient.__validateLoaderConfig(local)
    assert 'not found' in str(e_info)

    # all timeTuples values are Number
    with pytest.raises(Exception) as e_info:
        local = copy.deepcopy(baseConfig)
        local['loaderConfig']['mapping']['timeTuples'][0]['valueColumn'] = 'String'
        dv_pyclient.__validateLoaderConfig(local)
    assert 'must be a number' in str(e_info)


def test__validateLoaderConfig_dataFrameTypeCheck():
    df = pd.DataFrame({
        'String': pd.Categorical(['a', 'a', 'b', 'a']),
        'Date': pd.Timestamp('20130102'),
        'Value': np.array([3] * 4, dtype='int32')
    })
    config = dv_pyclient.__generateDataSourceLoaderConfig(df, '', '', None, [], [])

    # Each referenced col must exist in the data frame
    with pytest.raises(Exception) as e_info:
        noDateFrame = pd.DataFrame({
            'String': pd.Categorical(['a', 'a', 'b', 'a']),
            'Value': np.array([3] * 4, dtype='int32')
        })
        dv_pyclient.__validateLoaderConfig(config, noDateFrame)
    assert 'data frame missing required field: Date' in str(e_info)

    # Each referenced col must be the correct type
    with pytest.raises(Exception) as e_info:
        wrongTypeFrame = pd.DataFrame({
            'String': pd.Timestamp('20130102'),
            'Date': pd.Timestamp('20130102'),
            'Value': np.array([3] * 4, dtype='int32')
        })
        dv_pyclient.__validateLoaderConfig(config, wrongTypeFrame)
    assert 'ata frame field String must be of type StringColumnConfig.' in str(e_info)


def test__validateLoaderConfig_valid():
    # Completely valid config
    df = pd.DataFrame({
        'Date': pd.Timestamp('20130102'),
        'Value': np.array([3] * 4, dtype='int32')
    })
    assert dv_pyclient.__validateLoaderConfig(
        dv_pyclient.__generateDataSourceLoaderConfig(df, '', '', None, [], []),
        df
    )


def test_publish(session, dataFrame):
    dataSourceId = '72c221ff-703e-11ea-9c7f-1fc811f9ee94'
    resp = dv_pyclient.publish(session, dataSourceId, dataFrame)
    assert resp.status_code == 200


def test_command_line_interface():
    '''Test the CLI.'''
    runner = CliRunner()
    result = runner.invoke(cli.main)
    assert result.exit_code == 0
    assert 'dv_pyclient.cli.main' in result.output
    help_result = runner.invoke(cli.main, ['--help'])
    assert help_result.exit_code == 0
    assert '--help  Show this message and exit.' in help_result.output

def test___getDataFrameSample():
    sampleFrame = pd.DataFrame({
        'CatA': pd.Categorical(['A', 'A', 'B', 'B', 'C']),
        'CatB': pd.Categorical(['X', 'Y', 'X', 'Y', 'Z']),
        'Date': pd.Timestamp('20130102'),
        'Value': np.array(5, dtype='int32')
    })
    sample = dv_pyclient.__getDataFrameSample(sampleFrame)

    # Sampled every row
    assert len(sample['sampleData']) == 5

    # Per-column samples
    assert sample['columnSamples']['CatA'] == list(sampleFrame['CatA'])
    assert sample['columnSamples']['CatB'] == list(sampleFrame['CatB'])
    assert sample['columnSamples']['Date'] == list(map(str, sampleFrame['Date']))
    assert sample['columnSamples']['Value'] == list(map(str, sampleFrame['Value']))
