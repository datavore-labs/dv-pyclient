"""Main module."""
import ndjson
import requests
import jwt
import getpass
import numpy as np
import pandas as pd
import copy


def generate_meta(lines_in):
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


def df_empty(columns, dtypes, index=None):
    assert len(columns)==len(dtypes)
    df = pd.DataFrame(index=index)
    for c,d in zip(columns, dtypes):
        df[c] = pd.Series(dtype=d)
    return df


def _load_df(lines_in):
    key_columns, time_columns, value_columns, dtype = generate_meta(lines_in)
    df = df_empty(list(key_columns + time_columns + value_columns), dtype)
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


class Session:
    user_name = None
    user = None
    token = None
    env_conf = None

    def __init__(self, user_name, env_conf):
        self.user_name = user_name
        self.env_conf = env_conf

    def set_user(self, user):
        self.user = user

    def set_token(self, token):
        self.token = token


def _login(user_name=None, env_conf=None):
    password = getpass.getpass(prompt=f'Enter password for user {user_name} :')

    if user_name is not None and password is not None and env_conf is not None:
        res = requests.get(env_conf['authDomain'], auth=(user_name, password))
        if res.status_code == 200:
            result_json = res.json()
            token = result_json['nextToken']
            user = jwt.decode(token, verify=False)
            print(f'Login success for {user["fullName"]}\n')
            result = Session(user_name, env_conf)
            result.set_user(user)
            result.set_token(token)
            return result
        else:
            raise Exception(res.status_code, res.content.decode('ascii'))
    else:
        print("Requires username, password and data_config from Datavore UI")


def _get_data(session: Session, step_info=None):
    """
    1. Make request using token.
    1a. if response is 200OK, return data as pandas frame
    1b. if response 401Unauthorized try login and return data frame
    1c. if response is any other
            throw exception
    Session that contains information to re-authenticate if required.
    :param session:
    :param step_info: Some JSON to post
    :return:
    """
    auth_header = {
        'Authorization': 'Bearer %s' % session.token,
        'Content-type': 'application/json',
    }

    res = requests.post(session.env_conf['apiDomain'], json=step_info, headers=auth_header)
    if res.status_code == 200:
        payload = res.json(cls=ndjson.Decoder)
        return payload
    elif res.status_code == 401:
        session = _login(session.user_name, session.env_conf)
        return _get_data(session, step_info)
    else:
        raise Exception(res.status_code, res.content.decode('ascii'))


