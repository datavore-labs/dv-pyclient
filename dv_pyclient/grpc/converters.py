'''
Converter methods for operating between gRPC messages and datavore domain objects
'''

import dv_pyclient.grpc.dataSources_pb2 as msg
from dv_pyclient.grpc.util import str_value_or_none, str_opt_grpc

def __string_config_dv_to_grpc(config):
    return msg.ColumnConfig(stringColumnConfig=msg.StringColumnConfig(
        name = config['name'],
        displayLabel = config['name'],
        modifier = None,
        ontology = None
    ))

def __static_string_config_dv_to_grpc(config):
    return msg.ColumnConfig(staticStringColumnConfig=msg.StaticStringColumnConfig(
        name = config['name'],
        displayLabel = config['name'],
        value = config['value'],
        modifier = None,
        ontology = None
    ))

def __number_config_dv_to_grpc(config):
    return msg.ColumnConfig(numberColumnConfig=msg.NumberColumnConfig(
        name = config['name'],
        displayLabel = config['name']
    ))

def __static_number_config_dv_to_grpc(config):
    return msg.ColumnConfig(staticNumberColumnConfig=msg.StaticNumberColumnConfig(
        name = config['name'],
        displayLabel = config['name'],
        value = config['value'],
    ))

def __time_config_dv_to_grpc(config):
    return msg.ColumnConfig(timeColumnConfig=msg.TimeColumnConfig(
        name = config['name'],
        displayLabel = config['name']
    ))

def __static_time_config_dv_to_grpc(config):
    return msg.ColumnConfig(staticTimeColumnConfig=msg.StaticTimeColumnConfig(
        name = config['name'],
        displayLabel = config['name'],
        value = config['value']
    ))

dv_column_config_to_grpc_map = {
    'StringColumnConfig': __string_config_dv_to_grpc,
    'StaticStringColumnConfig': __static_string_config_dv_to_grpc,
    'NumberColumnConfig': __number_config_dv_to_grpc,
    'StaticNumberColumnConfig': __static_number_config_dv_to_grpc,
    'TimeColumnConfig': __time_config_dv_to_grpc,
    'StaticTimeColumnConfig': __static_time_config_dv_to_grpc,
}

def dv_column_config_to_grpc(config) -> msg.ColumnConfig:
    if not config['dataType'] in dv_column_config_to_grpc_map:
        raise RuntimeError(f'Cannot process {config["dataType"]} no matching gRPC message.')

    return dv_column_config_to_grpc_map[config['dataType']](config)

def dv_time_tuple_to_grpc(time_tuple) -> msg.TimeTupleConfig:
    return msg.TimeTupleConfig(
        timeColumn = time_tuple['timeColumn'],
        valueColumn = time_tuple['valueColumn']
    )

def dv_load_mapping_to_grpc(mapping) -> msg.DataLoadMapping:
    converted_time_tuples = [dv_time_tuple_to_grpc(value) for value in mapping['timeTuples']]
    return msg.DataLoadMapping(
        keyColumns = mapping['keyColumns'],
        valueModifiers = mapping['valueModifiers'],
        timeColumns = mapping['timeColumns'],
        frequency = str_value_or_none(mapping['frequency']),
        valueLabelColumn = mapping['valueLabelColumn'],
        timeTuples = converted_time_tuples
    )

def dv_row_sample_to_grpc(row) -> msg.RowSample:
    grpc_values = [str_opt_grpc(value) for value in row]
    return msg.RowSample(values = grpc_values)

def dv_column_sample_to_grpc(name, sample) -> msg.ColumnSample:
    return msg.ColumnSample(
        columnName = name,
        values = sample
    )
