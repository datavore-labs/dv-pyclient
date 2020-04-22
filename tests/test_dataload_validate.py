#!/usr/bin/env python

'''test client.publish flows for uploading a data frame'''

import pytest
import copy
import numpy as np
import pandas as pd

import dv_pyclient.dataload._domain as domain
from dv_pyclient.dataload.validate import validate_data_loader


def __generate_cfg(df):
    column_configs = domain.get_column_configs(df)
    data_source_meta = domain.ds_meta(
        data_source_id = 'ds-id',
        datasource = 'pytest',
        publisher = 'pytest',
        dataset = 'data frame'
    )
    loader_config = domain.csv_loader_config(
        source_settings = domain.csv_source_settings(column_configs),
        mapping = domain.simple_load_mapping(column_configs),
        data_source_meta = data_source_meta
    )
    return domain.csv_data_loader('ds-id', loader_config)


def test_empty():
    # No config
    with pytest.raises(Exception) as e_info:
        validate_data_loader({})
    assert 'Empty loader config' in str(e_info)


def test_no_time():
    # No time columns
    with pytest.raises(Exception) as e_info:
        df = pd.DataFrame({})
        validate_data_loader(
            __generate_cfg(df)
        )
    assert 'Loader config requires non-empty time columns.' in str(e_info)


def test_no_tuples():
    # No time/value tuples
    with pytest.raises(Exception) as e_info:
        df = pd.DataFrame({
            'String': pd.Categorical(['a', 'a', 'b', 'a']),
            'Date': pd.Timestamp('20130102')
        })
        validate_data_loader(
            __generate_cfg(df)
        )
    assert 'Time tuples empty. No column loaded.' in str(e_info)


def test_config_type_check():
    df = pd.DataFrame({
        'String': pd.Categorical(['a', 'a', 'b', 'a']),
        'Date': pd.Timestamp('20130102'),
        'Value': np.array([3] * 4, dtype='int32')
    })
    baseConfig = __generate_cfg(df)

    # all keyColumns defined
    with pytest.raises(Exception) as e_info:
        local = copy.deepcopy(baseConfig)
        local['loaderConfig']['mapping']['keyColumns'] = ['NotAField']
        validate_data_loader(local)
    assert 'key column NotAField not found' in str(e_info)

    # all keyColumns are strings
    with pytest.raises(Exception) as e_info:
        local = copy.deepcopy(baseConfig)
        local['loaderConfig']['mapping']['keyColumns'] = ['Date']
        validate_data_loader(local)
    assert 'key column Date must be a string' in str(e_info)

    # all valueLabelColumn are defined
    with pytest.raises(Exception) as e_info:
        local = copy.deepcopy(baseConfig)
        local['loaderConfig']['mapping']['valueLabelColumn'] = ['NotAField']
        validate_data_loader(local)
    assert 'value label NotAField not found' in str(e_info)

    # all valueLabelColumn are strings
    with pytest.raises(Exception) as e_info:
        local = copy.deepcopy(baseConfig)
        local['loaderConfig']['mapping']['valueLabelColumn'] = ['Date']
        validate_data_loader(local)
    assert 'value label Date must be a string' in str(e_info)

    # all timeColumns are defined
    with pytest.raises(Exception) as e_info:
        local = copy.deepcopy(baseConfig)
        local['loaderConfig']['mapping']['timeColumns'] = ['NotAField']
        validate_data_loader(local)
    assert 'time column NotAField not found' in str(e_info)

    # all timeColumns are time
    with pytest.raises(Exception) as e_info:
        local = copy.deepcopy(baseConfig)
        local['loaderConfig']['mapping']['timeColumns'] = ['String']
        validate_data_loader(local)
    assert 'time column String must be a time' in str(e_info)

    # all timeTuples times are defined
    with pytest.raises(Exception) as e_info:
        local = copy.deepcopy(baseConfig)
        local['loaderConfig']['mapping']['timeTuples'][0]['timeColumn'] = 'NotAField'
        validate_data_loader(local)
    assert 'not found' in str(e_info)

    # all timeTuples times are time
    with pytest.raises(Exception) as e_info:
        local = copy.deepcopy(baseConfig)
        local['loaderConfig']['mapping']['timeTuples'][0]['timeColumn'] = 'String'
        validate_data_loader(local)
    assert 'must be a time' in str(e_info)

    # all timeTuples values are defined
    with pytest.raises(Exception) as e_info:
        local = copy.deepcopy(baseConfig)
        local['loaderConfig']['mapping']['timeTuples'][0]['valueColumn'] = 'NotAField'
        validate_data_loader(local)
    assert 'not found' in str(e_info)

    # all timeTuples values are Number
    with pytest.raises(Exception) as e_info:
        local = copy.deepcopy(baseConfig)
        local['loaderConfig']['mapping']['timeTuples'][0]['valueColumn'] = 'String'
        validate_data_loader(local)
    assert 'must be a number' in str(e_info)


def test_data_frame_type_check():
    df = pd.DataFrame({
        'String': pd.Categorical(['a', 'a', 'b', 'a']),
        'Date': pd.Timestamp('20130102'),
        'Value': np.array([3] * 4, dtype='int32')
    })
    config = __generate_cfg(df)

    # Each referenced col must exist in the data frame
    with pytest.raises(Exception) as e_info:
        noDateFrame = pd.DataFrame({
            'String': pd.Categorical(['a', 'a', 'b', 'a']),
            'Value': np.array([3] * 4, dtype='int32')
        })
        validate_data_loader(config, noDateFrame)
    assert 'data frame missing required field: Date' in str(e_info)

    # Each referenced col must be the correct type
    with pytest.raises(Exception) as e_info:
        wrongTypeFrame = pd.DataFrame({
            'String': pd.Timestamp('20130102'),
            'Date': pd.Timestamp('20130102'),
            'Value': np.array([3] * 4, dtype='int32')
        })
        validate_data_loader(config, wrongTypeFrame)
    assert 'ata frame field String must be of type StringColumnConfig.' in str(e_info)


def test_valid_config():
    # Completely valid config
    df = pd.DataFrame({
        'Date': pd.Timestamp('20130102'),
        'Value': np.array([3] * 4, dtype='int32')
    })
    assert validate_data_loader(
        __generate_cfg(df),
        df
    )
