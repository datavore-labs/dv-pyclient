#!/usr/bin/env python

'''Testing dataframe utilities'''

import pytest

import numpy as np
import pandas as pd
import dv_pyclient.dataframe.util as df_util


def test_dataframe_util_get_sample():
    sample_df = pd.DataFrame({
        'CatA': pd.Categorical(['A', 'A', 'B', 'B', 'C']),
        'CatB': pd.Categorical(['X', 'Y', 'X', 'Y', 'Z']),
        'Date': pd.Timestamp('20130102'),
        'Value': np.array(5, dtype='int32')
    })
    sample = df_util.get_sample(sample_df)

    # Sampled every row
    assert len(sample['sampleData']) == 5

    # Per-column samples should be entire set
    assert set(sample['columnSamples'].keys()) == set(sample_df.columns)
