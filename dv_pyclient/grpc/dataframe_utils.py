'''
Utilities for connecting datavore, dataframes, and gRPC
'''

from typing import Generator, List
import math
import numpy as np
import dv_pyclient.grpc.dataSources_pb2 as msg
import google.protobuf.wrappers_pb2 as proto
import dv_pyclient.grpc.util as util
import dv_pyclient.grpc.converters as convert
import dv_pyclient.dataload._domain as dv_dataload
from dv_pyclient.dataframe.util import ts_to_unix_epoch_seconds, get_sample as get_df_sample

import logging
logging.basicConfig(
    format='[%(asctime)s] {%(filename)s:%(lineno)d} %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

def serialize_data_frame(df, project_cols: List[msg.ProjectColumn], chunk_size = 100) -> Generator[msg.DataRecordsReply, None, None]:
    '''
    Iterate a dataframe's rows as api.DataRecordsReply
    !!! time columns must be converted to int BEFORE this method is called !!!

    Immutable on df

    :param df: DataFrame -
    :param project_cols: ProjectColumn[] - columns and type order to keep things aligned
    :param chunk_size: Int - Optional chunking size for record arrays
    '''
    string_names = [
        x.name
        for x in project_cols
        if util.is_string_column_type(x.type)
    ]
    string_dict = {
        col_name : index
        for (index, col_name) in enumerate(string_names)
    }

    number_names = [
        x.name
        for x in project_cols
        if util.is_number_column_type(x.type)
    ]
    number_dict = {
        col_name : index
        for (index, col_name) in enumerate(number_names)
    }

    time_names = [
        x.name
        for x in project_cols
        if util.is_time_column_type(x.type)
    ]
    time_dict = {
        col_name : index
        for (index, col_name) in enumerate(time_names)
    }

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


def generate_data_frame_uniques(df, request: msg.DataSourceQueryRequest, chunk_size = 100) -> Generator[msg.DataRecordsReply, None, None]:
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

def generate_data_frame_meta(df, name, request: msg.DataSourceMetaRequest) -> msg.DataSourceMetaReply:
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

def make_line_query(query: msg.QueryFilter) -> str:
    '''
    Convert a filter to a query predicate to pass into pandas data frame query
    '''

    # String filters are or'd of each of the cols (is this true...?)
    if len(query.stringFilter.stringFilter) > 0:
        return ' or '.join(
            f'{query.stringFilter.name} == "{strFilter.value.value}"' for strFilter in query.stringFilter.stringFilter
        )

    # @todo: other filters
    return ''


def query_data_frame(df, request: msg.DataSourceQueryRequest) -> Generator[msg.DataRecordsReply, None, None]:
    '''
    Applies a set of queries to the given data frame and yields the records

    !!! Mutates DF (sorts on time on query result) !!!
    '''
    # Grab the projections we care about
    project_names = [x.name for x in request.projectColumns]

    # Grab our string + time projections to sort byt
    string_names = [
        x.name
        for x in request.projectColumns
        if util.is_string_column_type(x.type)
    ]

    time_names = [
        x.name
        for x in request.projectColumns
        if util.is_time_column_type(x.type)
    ]

    for line_query in request.lineQueries:
        # Apply the line query to filter to
        filterExprs = [make_line_query(query) for query in line_query.filters]
        line_query = ' and '.join(filterExprs)
        logger.info(f'Line query: {line_query}')

        # Filter data + sort by time
        line_result_df = df[project_names].query(line_query)
        # !! Mutates !!
        line_result_df.sort_values(by=string_names + time_names, inplace=True)

        # Send our batch -- do it in 1 chunk
        num_rows = line_result_df.shape[0]
        yield from serialize_data_frame(line_result_df, request.projectColumns, num_rows)
