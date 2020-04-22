'''
Helpers and methods around gRPC messages
'''

import google.protobuf.wrappers_pb2 as proto
from dv_pyclient.grpc import dataSources_pb2 as msg

def is_string_column_type(columnType):
    return columnType == msg.ColumnType.Value('String')

def is_time_column_type(columnType):
    return columnType == msg.ColumnType.Value('Time')

def is_number_column_type(columnType):
    return columnType == msg.ColumnType.Value('Number')

def column_type_to_string(projectedColumn):
    if is_string_column_type(projectedColumn.type):
        return 'String'
    if is_time_column_type(projectedColumn.type):
        return 'Time'
    if is_number_column_type(projectedColumn.type):
        return 'Number'
    raise Exception(f'Unhandled column type? {projectedColumn.type}')

def str_value_or_none(value):
    if value == None:
        return None
    return proto.StringValue(value=value)

def str_opt_grpc(value):
    if value == None:
        return msg.OptionalString(value = None)
    return msg.OptionalString(value = proto.StringValue(value = value))
