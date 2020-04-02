"""Main module."""

import io
import tempfile
import ndjson
import requests
import jwt
import getpass
import numpy as np
import pandas as pd
import copy

from pandas.core.dtypes.common import (
    is_string_dtype,
    is_numeric_dtype,
    is_datetime64_any_dtype,
)


def __generate_meta(lines_in):
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


def __df_empty(columns, dtypes, index=None):
    assert len(columns) == len(dtypes)
    df = pd.DataFrame(index=index)
    for c, d in zip(columns, dtypes):
        df[c] = pd.Series(dtype=d)
    return df


def __getColumnTypeOptions(dType):
    if(is_numeric_dtype(dType)):
        return {
            'dataType': 'NumberColumnConfig',
        }
    if(is_string_dtype(dType)):
        return {
            'dataType': 'StringColumnConfig',
        }
    if(is_datetime64_any_dtype(dType)):
        return {
            "dateFormat": "ISO_DATE",
            'dataType': 'TimeColumnConfig',
        }
    raise Exception('Unsupprted dType: {}'.format(dType))


def __getColumnConfigs(df):
    columnConfigs = []
    for name, dType in df.dtypes.items():
        baseConfig = __getColumnTypeOptions(dType)
        baseConfig.update({
            'name': name,
            'displayLabel': name,
        })
        columnConfigs.append(baseConfig)
    return columnConfigs


def __csvFileSettings(columnConfigs):
    return {
        'filePath': 'from dataframe',
        'delimiter': ',',
        'lineSeparator': '\n',
        'quote': '"',
        'quoteEscape': '"',
        'columnConfigs': columnConfigs,
    }


def __dataLoadMapping(keyColumns, valueModifiers, timeColumns, frequency, valueLabelColumn, timeTuples):
    return {
        'keyColumns': keyColumns,
        'valueModifiers': valueModifiers,
        'timeColumns': timeColumns,
        'frequency': frequency,
        'valueLabelColumn': valueLabelColumn,
        'timeTuples': timeTuples,
    }


def __datasourceMeta(datasourceId, datasource, publisher, dataset, readGroups):
    return {
        'DATA_SOURCE_ID': datasourceId,
        'DATA_SOURCE': datasource,
        'PUBLISHER': publisher,
        'DATASET': dataset,
        'readGroups': readGroups,
    }


def __generateDataSourceLoaderConfig(df, userName, dataSourceId, frequency, valueModifiers, valueLabelColumn):
    columnConfigs = __getColumnConfigs(df)
    stringColumns = list(
        filter(lambda c: c['dataType'] == 'StringColumnConfig', columnConfigs))
    keyColumns = list(filter(lambda s: not (
        s in valueModifiers or s in valueModifiers), stringColumns))
    timeColumns = list(
        filter(lambda c: c['dataType'] == 'TimeColumnConfig', columnConfigs))
    valueColumns = list(
        filter(lambda c: c['dataType'] == 'NumberColumnConfig', columnConfigs))
    timeTuples = []
    for v in valueColumns:
        for t in timeColumns:
            timeTuples.append(
                {'timeColumn': t['name'], 'valueColumn': v['name']})
    csvConfig = {
        'generated': True,
        'sourceSettings': __csvFileSettings(columnConfigs),
        'mapping': __dataLoadMapping(
            keyColumns=list(map(lambda i: i['name'], keyColumns)),
            timeColumns=list(map(lambda i: i['name'], timeColumns)),
            valueLabelColumn=list(map(lambda i: i['name'], valueLabelColumn)),
            valueModifiers=valueModifiers,
            frequency=frequency,
            timeTuples=timeTuples
        ),
        'datasource': __datasourceMeta(dataSourceId, 'datasource', userName, 'dataset', []),
    }
    return {
        'type': 'CsvDataLoaderConfig',
        'dataSource': {
            'docType': 'DataSource',
            'id': dataSourceId,
        },
        'strategy': 'Overwrite',
        'loaderConfig': csvConfig,
        'inputs': {}
    }


def load_df(lines_in):
    key_columns, time_columns, value_columns, dtype = __generate_meta(lines_in)
    df = __df_empty(list(key_columns + time_columns + value_columns), dtype)
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


def login(user_name=None, env_conf=None, password=None):
    if password == None:
        password = getpass.getpass(
            prompt=f'Enter password for user {user_name} :')

    if user_name is not None and password is not None and env_conf is not None:
        res = requests.get(
            f'{env_conf["authDomain"]}/login', auth=(user_name, password))
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


def get_data(session: Session, step_info=None):
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

    res = requests.post(
        f'{session.env_conf["apiDomain"]}/exec/get-lines', json=step_info, headers=auth_header)
    if res.status_code == 200:
        payload = res.json(cls=ndjson.Decoder)
        return payload
    elif res.status_code == 401:
        session = login(session.user_name, session.env_conf)
        return get_data(session, step_info)
    else:
        raise Exception(res.status_code, res.content.decode('ascii'))


def __setDatasourceLoaderConfig(session: Session, dataSourceId, loaderConfig):
    auth_header = {
        'Authorization': 'Bearer %s' % session.token,
        'Content-type': 'application/json',
    }
    url = f'{session.env_conf["apiDomain"]}/server/txns/datasource/{dataSourceId}/loader'
    res = requests.post(url, headers=auth_header, json=loaderConfig)
    if res.status_code == 200:
        return res
    else:
        raise Exception(res.status_code, res.content.decode('ascii'))


def __getPreSignedUrl(session: Session, dataSourceId):
    auth_header = {
        'Authorization': 'Bearer %s' % session.token,
        'Content-type': 'application/json',
    }
    params = {'dataSourceId': dataSourceId, 'extension': '.csv'}
    url = f'{session.env_conf["apiDomain"]}/server/dataload/csvUploadUrl'
    res = requests.get(url, headers=auth_header, params=params)
    if res.status_code == 200:
        return res.json()['payload']['presignedUrl']
    else:
        raise Exception(res.status_code, res.content.decode('ascii'))

def __cancelCurrentLoad(session: Session, dataSourceId):
    auth_header = {
        'Authorization': 'Bearer %s' % session.token,
        'Content-type': 'application/json',
    }
    url = f'{session.env_conf["apiDomain"]}/server/task/cancel/DATALOADER_{dataSourceId}'
    res = requests.delete(url, headers=auth_header)
    if res.status_code == 200:
        return res.json()['payload']
    else:
        raise Exception(res.status_code, res.content.decode('ascii'))

def __validateLoaderConfig(loaderConfig):
    csvConfig = loaderConfig["loaderConfig"]
    if not csvConfig:
        raise Exception("Empty loader config")

    # Check mapping
    mapping = csvConfig["mapping"]
    if not mapping["timeColumns"]:
        raise Exception("Loader config requires non-empty time columns.")

    # Check time tuples nonempty
    if not mapping["timeTuples"]:
        raise Exception("Time tuples empty. No column loaded.")

    return True

def publish(session: Session, dataSourceId, df, frequency=None, valueModifiers=[], valueLabelColumn=[]):
    # Cancel load if it exists
    __cancelCurrentLoad(session, dataSourceId)

    # Generate + check config, set if passes
    loaderConfig = __generateDataSourceLoaderConfig(
        df, session.user_name, dataSourceId, frequency, valueModifiers, valueLabelColumn)
    __validateLoaderConfig(loaderConfig)
    __setDatasourceLoaderConfig(session, dataSourceId, loaderConfig)

    # Generate upload url + run it
    uploadUrl = __getPreSignedUrl(session, dataSourceId)

    # Put data to the uploadUrl
    with tempfile.NamedTemporaryFile(mode='r+') as temp:
        df.to_csv(temp.name, index=False)
        res = requests.put(uploadUrl, data=open(temp.name, mode='rb'))

        if res.status_code == 200:
            return res
        elif res.status_code == 401:
            session = login(session.user_name, session.env_conf)
            return publish(session, dataSourceId, df, frequency, valueModifiers, valueLabelColumn)
        else:
            raise Exception(res.status_code, res.content.decode('ascii'))
