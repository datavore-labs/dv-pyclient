'''
Utilities for connecting datavore, dataframes, and gRPC
'''

import math
import numpy as np
import dv_pyclient.grpc.dataSources_pb2 as msg
import google.protobuf.wrappers_pb2 as proto
import dv_pyclient.grpc.util as util
import dv_pyclient.grpc.converters as convert
import dv_pyclient.dataload._domain as dv_dataload
from dv_pyclient.dataframe.util import ts_to_unix_epoch_seconds, get_sample as get_df_sample

def serialize_data_frame(df, project_cols, chunk_size = 100):
    '''
    Generator.

    Iterate a dataframe's rows as api.DataRecordsReply
    !!! time columns must be converted to int BEFORE this method is called !!!

    Immutable on df

    :param df: DataFrame -
    :param project_cols: ProjectColumn[] - columns and type order to keep things aligned
    :param chunk_size: Int - Optional chunking size for record arrays
    '''
    string_project = list(filter(lambda x: util.is_string_column_type(x.type), project_cols))
    string_names = list(map(lambda x: x.name, string_project))
    string_dict = dict([(item, index) for (index, item) in enumerate(string_names)])

    number_project = list(filter(lambda x: util.is_number_column_type(x.type), project_cols))
    number_names = list(map(lambda x: x.name, number_project))
    number_dict = dict([(item, index) for (index, item) in enumerate(number_names)])

    time_project = list(filter(lambda x: util.is_time_column_type(x.type), project_cols))
    time_names = list(map(lambda x: x.name, time_project))
    time_dict = dict([(item, index) for (index, item) in enumerate(time_names)])

    num_rows = df.shape[0]
    for chunk_df in list(filter(lambda x: not x.empty, np.array_split(df, math.ceil(num_rows / chunk_size)))):
        data_records = []
        for _, row in chunk_df.iterrows():
            strings = [msg.OptionalString(value=proto.StringValue(value=None))] * len(string_names)
            numbers = [msg.OptionalNumber(value=proto.DoubleValue(value=None))] * len(number_names)
            times = [msg.OptionalTime(value=proto.Int64Value(value=None))] * len(time_names)

            for col in project_cols:
                # Strings
                if util.is_string_column_type(col.type):
                    if row[col.name] == None:
                        strings[string_dict[col.name]] = msg.OptionalString(value=None)
                    else:
                        strings[string_dict[col.name]] = msg.OptionalString(value=proto.StringValue(value=row[col.name]))

                # Numbers
                elif util.is_number_column_type(col.type):
                    if row[col.name] == None or math.isnan(row[col.name]):
                        numbers[number_dict[col.name]] = msg.OptionalNumber(value=None)
                    else:
                        numbers[number_dict[col.name]] = msg.OptionalNumber(value=proto.DoubleValue(value=row[col.name]))

                # Times
                elif util.is_time_column_type(col.type):
                    if row[col.name] == None or math.isnan(row[col.name].value):
                        times[time_dict[col.name]] = msg.OptionalTime(value=None)
                    else:
                        times[time_dict[col.name]] = msg.OptionalTime(value=proto.Int64Value(value=ts_to_unix_epoch_seconds(row[col.name])))
            data_records.append(msg.DataRecord(strings=strings, numbers=numbers, times=times))
        yield msg.DataRecordsReply(records=data_records)


def generate_data_frame_uniques(df, request: msg.DataSourceQueryRequest, chunk_size = 100):
    '''
    Generic logic for handling uniques request on a data frame.
    Generates DataLoadRecord responses.

    Immutable on df
    '''
    df_names = list(map(lambda c:  c.name, request.projectColumns))
    stringsOnly = list(
        df[df_names].select_dtypes(include=['category', 'object']).columns
    )
    unique_df = df[df_names].drop_duplicates(subset=stringsOnly)
    # Run the serialize code
    yield from serialize_data_frame(unique_df, request.projectColumns, chunk_size)

def map_dv_config_to_grpc(column_config):
    '''Maps dv dataload domain column configs to gRPC messages'''
    msg.ColumnConfig()

def generate_data_frame_meta(df, name, request: msg.DataSourceMetaRequest):
    # Extract meta as we would for load
    column_configs = dv_dataload.get_column_configs(df)
    load_mapping = dv_dataload.simple_load_mapping(column_configs)
    sample = get_df_sample(df)

    # Convert to messages
    grpc_column_configs = [convert.dv_column_config_to_grpc(v) for v in column_configs]
    grpc_load_mapping = convert.dv_load_mapping_to_grpc(load_mapping)
    grpc_row_samples = [convert.dv_row_sample_to_grpc(v) for v in sample['sampleData']]
    grpc_column_samples = [convert.dv_column_sample_to_grpc(k, v) for k, v in sample['columnSamples'].items()]

    return msg.DataSourceMetaReply(
        dataSourceId=request.dataSourceId,
        dataSourceName=name,
        columnConfigs=grpc_column_configs,
        dataLoadMapping=grpc_load_mapping,
        sampleData=grpc_row_samples,
        columnSamples=grpc_column_samples
    )
