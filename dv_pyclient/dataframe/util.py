'''utilities for dataframes'''

import numpy as np
import pandas as pd
from dv_pyclient.util import to_str_none

def make_empty(column_names, column_dtypes, index=None):
    '''
    Create an empty dataframe with given names and types. Backed by empty series.

    :param column_names: List[String] - series names
    :param column_dtypes: List[String] - series dtypes
    :param index: - Optional index to pass into the DataFrame
    :return: DataFrame
    '''

    assert len(column_names) == len(column_dtypes)
    df = pd.DataFrame(index=index)
    for c, d in zip(column_names, column_dtypes):
        df[c] = pd.Series(dtype=d)
    return df


def get_sample(df, col_samples=25, row_samples=25):
    '''
    Gets a row-wise and column-wise sample of a DataFrame.
    Rows are as unique as possible.
    Dates are formatted as ISO strings
    Immutable on df

    :param DataFrame:
    :param col_samples: Int - Number of records to sample per-column
    :param row_samples: Int - Number of rows to sample
    :return: { sampleData, columnSamples }
    '''

    # get only string columns -- @todo: is object fine? data frames with mixed types are object (so, strings with null)
    stringsOnly = list(
        df.select_dtypes(include=['category', 'object']).columns
    )

    # get a distinct on strings sample
    unique_df = df.drop_duplicates(subset=stringsOnly)
    sampleData = unique_df.sample(min(unique_df.shape[0], row_samples))

    # format dates as iso strings
    datesOnly = list(
        sampleData.select_dtypes(include=[np.datetime64]).columns
    )
    sampleData[datesOnly] = sampleData[datesOnly].applymap(lambda x: x.isoformat())

    # first 25 unique non-null values of column c
    columnSamples = {}
    for c in df.columns:
        sample = df[c].dropna().sample(min(df.shape[0], col_samples))
        columnSamples[c] = list(map(str, sample))

    sampleValues = sampleData.where(pd.notnull(df), None).applymap(to_str_none).values.tolist()

    # Project values
    return {
        'sampleData': sampleValues,
        'columnSamples': columnSamples
    }

def ts_to_unix_epoch_seconds(time_stamp):
    return np.int_(time_stamp.value / 10**9)
