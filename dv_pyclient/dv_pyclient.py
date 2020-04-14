'''Main module.'''

import io
import json
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
    if (is_datetime64_any_dtype(dType)):
        return {
            'dateFormat': 'ISO_DATE_TIME',
            'dataType': 'TimeColumnConfig',
        }
    if (is_numeric_dtype(dType)):
        return {
            'dataType': 'NumberColumnConfig',
        }
    if (is_string_dtype(dType)):
        return {
            'dataType': 'StringColumnConfig',
        }
    raise Exception(f'Unsupprted dType: {dType}')


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


def __isTimeDataType(dataType):
    return dataType in frozenset(['TimeColumnConfig', 'StaticTimeConfig'])


def __isStringDataType(dataType):
    return dataType in frozenset(['StringColumnConfig', 'StaticStringConfig'])


def __isNumberDataType(dataType):
    return dataType in frozenset(['NumberColumnConfig', 'StaticNumberConfig'])


def __isStaticDataType(dataType):
    return dataType in frozenset(['StaticTimeConfig', 'StaticStringConfig', 'StaticNumberConfig'])


def __getDataLoadMappings(columnConfigs, valueModifiers):
    stringColumns = list(
        filter(lambda c: __isStringDataType(c['dataType']), columnConfigs))
    keyColumns = list(filter(lambda s: not (s in valueModifiers), stringColumns))
    timeColumns = list(
        filter(lambda c: __isTimeDataType(c['dataType']), columnConfigs))
    valueColumns = list(
        filter(lambda c: __isNumberDataType(c['dataType']), columnConfigs))
    timeTuples = []
    for v in valueColumns:
        for t in timeColumns:
            timeTuples.append(
                {'timeColumn': t['name'], 'valueColumn': v['name']}
            )

    return stringColumns, keyColumns, timeColumns, valueColumns, timeTuples


def __generateDataSourceLoaderConfig(df, userName, dataSourceId, frequency, valueModifiers, valueLabelColumn,
                                     sampleData=None, columnSamples=None):
    columnConfigs = __getColumnConfigs(df)
    stringColumns, keyColumns, timeColumns, valueColumns, timeTuples = __getDataLoadMappings(columnConfigs, valueModifiers)
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
        'sampleData': sampleData,
        'columnSamples': columnSamples,
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


def load_df(lines_in) -> pd.DataFrame:
    '''
    Load lines into a dataframe
    Returns a DataFrame
    '''
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
    '''
    Returns a valid datavore Session object
    '''
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
        print('Requires username, password and data_config from Datavore UI')


def get_data(session: Session, step_info=None):
    '''
    1. Make request using token.
    1a. if response is 200OK, return data as pandas frame
    1b. if response 401Unauthorized try login and return data frame
    1c. if response is any other
            throw exception
    Session that contains information to re-authenticate if required.
    :param session:
    :param step_info: Some JSON to post
    :return:
    '''
    auth_header = {
        'Authorization': 'Bearer %s' % session.token,
        'Content-type': 'application/json',
    }

    res = requests.post(
        f'{session.env_conf["execDomain"]}/get-lines', json=step_info, headers=auth_header)
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
    url = f'{session.env_conf["apiDomain"]}/txns/datasource/{dataSourceId}/loader'
    res = requests.post(url, headers=auth_header, json=loaderConfig)
    if res.status_code == 200:
        return res
    else:
        raise Exception(res.status_code, res.content.decode('ascii'))

def __getDatasourceLoaderConfig(session: Session, dataSourceId):
    auth_header = {
        'Authorization': 'Bearer %s' % session.token,
        'Content-type': 'application/json',
    }
    url = f'{session.env_conf["apiDomain"]}/txns/datasource/{dataSourceId}/loader'
    res = requests.get(url, headers=auth_header)
    if res.status_code == 200:
        return res.json()['payload']['document']['config']
    else:
        raise Exception(res.status_code, res.content.decode('ascii'))

def getPublishStatus(session: Session, dataSourceId):
    auth_header = {
        'Authorization': 'Bearer %s' % session.token,
        'Content-type': 'application/json',
    }
    url = f'{session.env_conf["apiDomain"]}/txns/datasource/{dataSourceId}/loader'
    res = requests.get(url, headers=auth_header)
    if res.status_code == 200:
        statusJson = res.json()['payload']['document']['status']

        if statusJson.get('status') == 'rejected':
            return {
                'status': statusJson.get('status'),
                'reason': statusJson.get('reason')
            }

        return { 'status': statusJson.get('status') }
    else:
        raise Exception(res.status_code, res.content.decode('ascii'))

def __getPreSignedUrl(session: Session, dataSourceId):
    auth_header = {
        'Authorization': 'Bearer %s' % session.token,
        'Content-type': 'application/json',
    }
    params = {'dataSourceId': dataSourceId, 'extension': '.csv'}
    url = f'{session.env_conf["apiDomain"]}/dataload/csvUploadUrl'
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
    url = f'{session.env_conf["apiDomain"]}/task/cancel/DATALOADER_{dataSourceId}'
    res = requests.delete(url, headers=auth_header)
    if res.status_code == 200:
        return res.json()['payload']
    else:
        raise Exception(res.status_code, res.content.decode('ascii'))


def __getColumnsByName(columnConfigs):
    return dict(
        map(lambda x: (x['name'], x), columnConfigs)
    )


def __validateLoaderConfig(loaderConfig, df=None):
    csvConfig = loaderConfig.get('loaderConfig')
    if not csvConfig:
        raise Exception('Empty loader config')

    # Check mapping
    mapping = csvConfig.get('mapping')
    if not mapping.get('timeColumns'):
        raise Exception('Loader config requires non-empty time columns.')

    # Check time tuples nonempty
    if not mapping.get('timeTuples'):
        raise Exception('Time tuples empty. No column loaded.')

    columnByName = __getColumnsByName(csvConfig['sourceSettings']['columnConfigs'])

    # Collectors for referenced cols
    requiredFields = set()

    # Check all columns are correct types and all are defined
    for field in mapping['keyColumns']:
        requiredFields.add(field)
        if not columnByName.get(field):
            raise Exception(f'key column {field} not found.')

        fieldType = columnByName[field]['dataType']
        if not __isStringDataType(fieldType):
            raise Exception(f'key column {field} must be a string, got {fieldType}.')

    # Check all value label are correct types and all are defined
    for field in mapping['valueLabelColumn']:
        requiredFields.add(field)
        if not columnByName.get(field):
            raise Exception(f'value label {field} not found.')

        fieldType = columnByName[field]['dataType']
        if not __isStringDataType(fieldType):
            raise Exception(f'value label {field} must be a string, got {fieldType}.')

    # Check all time columns label are correct types and all are defined
    for field in mapping['timeColumns']:
        requiredFields.add(field)
        if not columnByName.get(field):
            raise Exception(f'time column {field} not found.')

        fieldType = columnByName[field]['dataType']
        if not __isTimeDataType(fieldType):
            raise Exception(f'time column {field} must be a time, got {fieldType}.')

    # Check all time tuples
    for timeTuple in mapping['timeTuples']:
        requiredFields.add(timeTuple['timeColumn'])
        requiredFields.add(timeTuple['valueColumn'])

        if not columnByName.get(timeTuple['timeColumn']):
            raise Exception(f'time column in tuple {str(timeTuple)} not found.')

        timeType = columnByName[timeTuple['timeColumn']]['dataType']
        if not __isTimeDataType(timeType):
            raise Exception(f'time column in tuple {str(timeTuple)} must be a time, got {timeType}.')

        if not columnByName.get(timeTuple['valueColumn']):
            raise Exception(f'value column in tuple {str(timeTuple)} not found.')

        valueType = columnByName.get(timeTuple['valueColumn'])['dataType']
        if not __isNumberDataType(valueType):
            raise Exception(f'value column in tuple {str(timeTuple)} must be a number, got {valueType}.')

    # Check data frame fields and types
    if not df is None:
        dfColumnsByName = __getColumnsByName(__getColumnConfigs(df))
        for keyField in filter(lambda x: not __isStaticDataType(columnByName[x]['dataType']), requiredFields):
            requiredType = columnByName[keyField]['dataType']
            if not dfColumnsByName.get(keyField):
                raise Exception(f'data frame missing required field: {keyField} of type: {requiredType}')

            if dfColumnsByName[keyField]['dataType'] != requiredType:
                raise Exception(
                    f'data frame field {keyField} must be of type {requiredType}. Got {dfColumnsByName[keyField]["dataType"]}')

    return True


def publish(session: Session, dataSourceId, df):
    # Get the current loader config
    currentConfig = __getDatasourceLoaderConfig(session, dataSourceId)

    # Validate the config against the dataframe
    if not __validateLoaderConfig(currentConfig, df):
        raise Exception('Could not validate config.')

    # Cancel load if it exists
    try:
        __cancelCurrentLoad(session, dataSourceId)
    except:
        print('No job to cancel. Continuing.')
        # @todo: log debug here -- exception if never loaded before

    # Generate upload url
    uploadUrl = __getPreSignedUrl(session, dataSourceId)

    print('Uploading data frame...')

    # Update the config with the URL @todo: use patch so we don't send the entire data brick back up :/
    # currentConfig['uploadUrl'] = uploadUrl
    # __setDatasourceLoaderConfig(session, dataSourceId, currentConfig)

    # Put data to the uploadUrl
    retries = 2
    with tempfile.NamedTemporaryFile(mode='r+') as temp:
        df.to_csv(temp.name, index=False, date_format='%Y-%m-%dT%H:%M:%SZ')

        while retries > 0:
            with open(temp.name, mode='rb') as csvFile:
                res = requests.put(uploadUrl, data=csvFile)
                if res.status_code == 200:
                    print('Data frame uploaded. Datavore load started.')
                    return res
                elif res.status_code == 401:
                    retries -= 1
                    print(f'Session upload error. Log in again. Attempts remaining: {retries}')
                    session = login(session.user_name, session.env_conf)
                else:
                    raise Exception(res.status_code, res.content.decode('ascii'))

        # Ran out of retries and never managed to upload :(
        raise Exception('Failed to upload.')

def __toStrNone(s):
    if s is None:
        return None
    return str(s)

def __getDataFrameSample(df, colToSample=25, rowsToSample=25):
    # get only string columns -- @todo: is object fine? data frames with mixed types are object (so, strings with null)
    stringsOnly = list(
        df.select_dtypes(include=['category', 'object']).columns
    )

    # get a distinct on strings sample
    sampleData = df.drop_duplicates(subset=stringsOnly).sample(min(len(df), rowsToSample))

    # format dates as iso strings
    datesOnly = list(
        sampleData.select_dtypes(include=[np.datetime64]).columns
    )
    sampleData[datesOnly] = sampleData[datesOnly].applymap(lambda x: x.isoformat())

    # first 25 unique non-null values of column c
    columnSamples = {}
    for c in df.columns:
        sample = df[c].dropna().sample(colToSample, replace=True)
        columnSamples[c] = list(map(str, sample))

    sampleValues = sampleData.where(pd.notnull(df), None).applymap(__toStrNone).values.tolist()

    # Project values
    return {
        'sampleData': sampleValues,
        'columnSamples': columnSamples
    }


def setDataSourceSample(session: Session, dataSourceId, df):
    # get the samples
    sample = __getDataFrameSample(df)
    # generate a loaderConfig
    loaderConfig = __generateDataSourceLoaderConfig(
        df,
        session.user_name,
        dataSourceId,
        frequency=None,
        valueModifiers=[],
        valueLabelColumn=[],
        sampleData=sample['sampleData'],
        columnSamples=sample['columnSamples']
    )
    # validate the loaderConfig
    __validateLoaderConfig(loaderConfig)

    # save the loaderConfig
    out = __setDatasourceLoaderConfig(session, dataSourceId, loaderConfig)
    print('Sample uploaded. Go to the Datavore client to review')
    return out
