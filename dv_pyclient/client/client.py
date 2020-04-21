import copy
import requests
import pandas as pd
import numpy as np

from ..dataframe.util import make_empty as make_empty_df
from ..auth.auth import Session

def __extract_line_meta(lines_in):
    '''
    Extracts (keys, time, value, dtype) from a set of lines.
    If lines have different keys, the resulting data frame will be sparse.

    :param lines_in: List[Line] - Datavore lines.
    '''
    key_columns = []
    time_columns = []
    value_columns = []
    dtype = []
    for line in lines_in:
        for key in line['keys']:
            key_col_name = key['label']
            if key_col_name not in key_columns:
                key_columns.append(key_col_name)
                dtype.append(np.str)
        time_col_name = line['time']
        if time_col_name not in time_columns:
            time_columns.append(time_col_name)
            dtype.append(np.int64)
        value_col_name = line['value']
        if value_col_name not in value_columns:
            value_columns.append(value_col_name)
            dtype.append(np.float64)
    return key_columns, time_columns, value_columns, dtype

def lines_to_df(lines_in) -> pd.DataFrame:
    '''
    Load Datavore lines into a pandas dataframe

    :param lines_in: List[Line] - Lines to transform into data frame
    :returns: Pandas.DataFrame of all lines passed in.
    '''

    key_columns, time_columns, value_columns, dtype = __extract_line_meta(lines_in)

    df = make_empty_df(list(key_columns + time_columns + value_columns), dtype)

    for line in lines_in:
        row_keys = {}
        time_key = line['time']
        value_key = line['value']
        for key in line['keys']:
            row_keys[key['label']] = key['value']
        for data_point in line['data']:
            base = copy.copy(row_keys)
            base[time_key] = pd.to_datetime(data_point[0], unit='ms')
            base[value_key] = data_point[1]
            df = df.append(base, ignore_index=True)

    index_columns = list(key_columns + time_columns)

    return df.pivot_table(
        index=index_columns
    ).reset_index()

def get_data(session: Session, step_info=None):
    '''
    Load data from the Datavore client.
    Can be turned into a Pandas data frame using lines_to_df.

    1. Make request using token.
    1a. if response is 200OK, return data as pandas frame
    1b. if response 401Unauthorized try login and return data frame
    1c. if response is any other
            throw exception
    Session that contains information to re-authenticate if required.

    :param session: Session
    :param step_info: The step to evaluate. Get this from the Datavore client.
    :return: List[Line]
    :raises Exception: on request failure
    '''
    auth_header = {
        'Authorization': 'Bearer %s' % session.token,
        'Content-type': 'application/json',
    }

    res = requests.post(
        f'{session.env_conf["execDomain"]}/get-lines',
        json=step_info,
        headers=auth_header
    )

    if res.status_code == 200:
        payload = res.json(cls=ndjson.Decoder)
        return payload

    if res.status_code == 401:
        session = login(session.user_name, session.env_conf)
        return get_data(session, step_info)

    raise Exception(res.status_code, res.content.decode('ascii'))

