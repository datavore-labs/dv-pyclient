'''Publish a DataFrame into Datavore as a data source'''

import requests
import tempfile
import dv_pyclient.auth.auth as dv_auth
import dv_pyclient.dataframe.util as df_util
import dv_pyclient.dataload._domain as dataload_domain
import dv_pyclient.dataload.validate as dataload_validate

def __get_pre_signed_url(session: dv_auth.Session, data_source_id):
    '''
    Private since we're not exposing this here yet -- go through UI for that.

    Using CSV upload flow internally to handle writing the DataFrame.
    '''
    auth_header = {
        'Authorization': 'Bearer %s' % session.token,
        'Content-type': 'application/json',
    }
    params = {'dataSourceId': data_source_id, 'extension': '.csv'}
    url = f'{session.env_conf["apiDomain"]}/dataload/csvUploadUrl'
    res = requests.get(url, headers=auth_header, params=params)
    if res.status_code == 200:
        return res.json()['payload']['presignedUrl']
    else:
        raise Exception(res.status_code, res.content.decode('ascii'))

def __cancel_data_load(session: dv_auth.Session, data_source_id):
    '''
    Attempts to cancel a current load.
    Idempotent, and we want to cancel before re-publishing
    '''
    auth_header = {
        'Authorization': 'Bearer %s' % session.token,
        'Content-type': 'application/json',
    }
    url = f'{session.env_conf["apiDomain"]}/task/cancel/DATALOADER_{data_source_id}'
    res = requests.delete(url, headers=auth_header)
    if res.status_code == 200:
        return res.json()['payload']
    else:
        raise Exception(res.status_code, res.content.decode('ascii'))


def get_publish_status(session: dv_auth.Session, data_source_id):
    '''
    Gets the status object of an ongoing publish operation.

    :param session: Session - The Datavore session to use
    :param data_source_id: String - The data source to get status for
    :return: { status: String, reason?: String } - The status object representing the load
    :raises Exception: on failed response
    '''
    auth_header = {
        'Authorization': 'Bearer %s' % session.token,
        'Content-type': 'application/json',
    }
    url = f'{session.env_conf["apiDomain"]}/txns/datasource/{data_source_id}/loader'
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

def set_data_loader_config(session: dv_auth.Session, data_source_id, data_loader):
    '''
    Saves a data loader config for a data source.
    '''
    auth_header = {
        'Authorization': 'Bearer %s' % session.token,
        'Content-type': 'application/json',
    }
    url = f'{session.env_conf["apiDomain"]}/txns/datasource/{data_source_id}/loader'
    res = requests.post(url, headers=auth_header, json=data_loader)
    if res.status_code == 200:
        return res
    else:
        raise Exception(res.status_code, res.content.decode('ascii'))

def get_data_loader_config(session: dv_auth.Session, data_source_id):
    auth_header = {
        'Authorization': 'Bearer %s' % session.token,
        'Content-type': 'application/json',
    }
    url = f'{session.env_conf["apiDomain"]}/txns/datasource/{data_source_id}/loader'
    res = requests.get(url, headers=auth_header)
    if res.status_code == 200:
        return res.json()['payload']['document']['config']
    else:
        raise Exception(res.status_code, res.content.decode('ascii'))

def set_data_source_sample(session: dv_auth.Session, data_source_id, df):
    '''
    Sets the sample for a data source.
    Once the sample is set, go to the Datavore client to configure the load.
    Immutable on input DataFrame

    :param session: Session - The Datavore session to use
    :param data_source_id: String - The data source to set the sample for
    :param df: - DataFrame to use as a sample source
    :return: response - The result from setting the sample. Not very useful.
    :raises Exception: on invalid DataFrame config or sample generation.
    '''
    # get the samples
    sample = df_util.get_sample(df)

    # Build our default config
    column_configs = dataload_domain.get_column_configs(df)
    data_source_meta = dataload_domain.ds_meta(
        data_source_id = data_source_id,
        datasource = 'python',
        publisher = session.user_name,
        dataset = 'data frame'
    )
    loader_config = dataload_domain.csv_loader_config(
        source_settings = dataload_domain.csv_source_settings(column_configs),
        mapping = dataload_domain.simple_load_mapping(column_configs),
        data_source_meta = data_source_meta,
        sample_data = sample['sampleData'],
        column_samples = sample['columnSamples']
    )
    data_loader = dataload_domain.csv_data_loader(data_source_id, loader_config)

    # Validate the config against the dataframe
    if not dataload_validate.validate_data_loader(data_loader, df):
        raise Exception('Could not validate config.')

    # save the loaderConfig
    out = set_data_loader_config(session, data_source_id, data_loader)
    print('Sample uploaded. Go to the Datavore client to review')
    return out


def publish(session: dv_auth.Session, dataSourceId, df):
    '''
    Publish a DataFrame to Datavore that was configured on the client
    '''
    # Get the current loader config
    currentConfig = get_data_loader_config(session, dataSourceId)

    # Validate the config against the dataframe
    if not dataload_validate.validate_data_loader(currentConfig, df):
        raise Exception('Could not validate config.')

    # Cancel load if it exists
    try:
        __cancel_data_load(session, dataSourceId)
    except:
        print('No job to cancel. Continuing.')
        # @todo: log debug here -- exception if never loaded before

    # Generate upload url
    uploadUrl = __get_pre_signed_url(session, dataSourceId)

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
                    session = dv_auth.login(session.user_name, session.env_conf)
                else:
                    raise Exception(res.status_code, res.content.decode('ascii'))

        # Ran out of retries and never managed to upload :(
        raise Exception('Failed to upload.')
