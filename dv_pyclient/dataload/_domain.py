'''
Internal models for data loading.

Has connector methods for working and loading data frames
'''

from pandas.core.dtypes.common import (
    is_string_dtype,
    is_numeric_dtype,
    is_datetime64_any_dtype,
)

def ds_doc_ref(data_source_id):
    '''
    Simple DocRef for a data source
    '''
    return {
        'docType': 'DataSource',
        'id': data_source_id,
    }

def ds_meta(data_source_id, datasource, publisher, dataset, read_groups = []):
    '''
    Simple meta object for our data sources.
    Used in various publish methods.
    '''
    return {
        'DATA_SOURCE_ID': data_source_id,
        'DATA_SOURCE': datasource,
        'PUBLISHER': publisher,
        'DATASET': dataset,
        'readGroups': read_groups,
    }

def time_tuple(time_column, value_column):
    return {
        'timeColumn': time_column,
        'valueColumn': value_column
    }

def load_mapping(key_columns = [], value_modifiers = [], time_columns = [], frequency = None, value_label_columns = [], time_tuples = []):
    '''
    Describes how the tabular data should load into lines.
    Modified in the Datavore client.
    '''
    return {
        'keyColumns': key_columns,
        'valueModifiers': value_modifiers,
        'timeColumns': time_columns,
        'frequency': frequency,
        'valueLabelColumn': value_label_columns,
        'timeTuples': time_tuples,
    }


def csv_source_settings(column_configs):
    '''
    Details about the file to load.
    Used for parsing the CSV during load.
    '''
    return {
        'filePath': 'from dataframe',
        'delimiter': ',',
        'lineSeparator': '\n',
        'quote': '"',
        'quoteEscape': '"',
        'columnConfigs': column_configs,
    }

def csv_loader_config(source_settings, mapping, data_source_meta, sample_data = {}, column_samples = []):
    '''
    The loaderConfig for a csv_data_loader
    '''
    return {
        'generated': True,
        'sourceSettings': source_settings,
        'mapping': mapping,
        'sampleData': sample_data,
        'columnSamples': column_samples,
        'datasource': data_source_meta,
    }

def csv_data_loader(data_source_id, loader_config):
    '''
    Config object for csv load.
    Used for CSV file upload and python data frame load.
    '''
    return {
        'type': 'CsvDataLoaderConfig',
        'dataSource': ds_doc_ref(data_source_id),
        'strategy': 'Overwrite',
        'loaderConfig': loader_config,
        'inputs': {}
    }


# ---------- misc load methods
time_config_data_types = frozenset(['TimeColumnConfig', 'StaticTimeConfig'])
def is_time_data_type(data_type):
    return data_type in time_config_data_types


string_config_data_types = frozenset(['StringColumnConfig', 'StaticStringConfig'])
def is_string_data_type(data_type):
    return data_type in string_config_data_types

number_config_data_types = frozenset(['NumberColumnConfig', 'StaticNumberConfig'])
def is_number_data_type(data_type):
    return data_type in number_config_data_types

static_config_data_types = frozenset(['StaticTimeConfig', 'StaticStringConfig', 'StaticNumberConfig'])
def is_static_data_type(data_type):
    return data_type in static_config_data_types


def dtype_to_column_config(dtype):
    if (is_datetime64_any_dtype(dtype)):
        return {
            'dateFormat': 'ISO_DATE_TIME',
            'dataType': 'TimeColumnConfig',
        }
    if (is_numeric_dtype(dtype)):
        return {
            'dataType': 'NumberColumnConfig',
        }
    if (is_string_dtype(dtype)):
        return {
            'dataType': 'StringColumnConfig',
        }
    raise Exception(f'Unsupprted dType: {dtype}')

def get_column_configs(df):
    '''Immutable on df'''
    column_configs = []

    for name, dtype in df.dtypes.items():
        config = dtype_to_column_config(dtype)
        config.update({
            'name': name,
            'displayLabel': name,
        })
        column_configs.append(config)

    return column_configs

def split_column_configs(column_configs):
    '''
    Helper to split column configs into (string_configs, time_configs, number_configs)
    '''
    string_configs = list(filter(
        lambda c: is_string_data_type(c['dataType']),
        column_configs
    ))
    time_configs = list(filter(
        lambda c: is_time_data_type(c['dataType']),
        column_configs
    ))
    number_configs = list(filter(
        lambda c: is_number_data_type(c['dataType']),
        column_configs
    ))

    return (string_configs, time_configs, number_configs)

def simple_load_mapping(column_configs):
    '''Simple data load mapping from column configs'''
    (strings, times, numbers) = split_column_configs(column_configs)

    time_tuples = []
    for v in numbers:
        for t in times:
            time_tuples.append(
                time_tuple(
                    time_column = t['name'],
                    value_column = v['name']
                )
            )

    return load_mapping(
        key_columns = list(map(lambda c: c['name'], strings)),
        time_columns = list(map(lambda c: c['name'], times)),
        time_tuples = time_tuples,
    )

def get_columns_by_name(column_configs):
    return dict(
        map(lambda x: (x['name'], x), column_configs)
    )
