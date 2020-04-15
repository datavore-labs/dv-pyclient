from dv_pyclient.grpc import dataSources_pb2 as api
from pandas.core.dtypes.common import (
    is_string_dtype,
    is_numeric_dtype,
    is_datetime64_any_dtype,
)
import pandas as pd
import google.protobuf.wrappers_pb2 as proto
from google.protobuf.json_format import MessageToJson
import numpy as np
import google
import math

def __isTimeDataType(dataType):
    return dataType in frozenset(['TimeColumnConfig', 'StaticTimeConfig'])


def __isStringDataType(dataType):
    return dataType in frozenset(['StringColumnConfig', 'StaticStringConfig'])


def __isNumberDataType(dataType):
    return dataType in frozenset(['NumberColumnConfig', 'StaticNumberConfig'])


def __isStaticDataType(dataType):
    return dataType in frozenset(['StaticTimeConfig', 'StaticStringConfig', 'StaticNumberConfig'])


def __getDataLoadMappings(columnConfigs, valueModifiers):
    stringColumnsAndMeta = list(filter(lambda c: __isStringDataType(c[1]['dataType']), columnConfigs))
    keyColumnsAndMeta = list(filter(lambda s: not (s in valueModifiers), stringColumnsAndMeta))
    timeColumnsAndMeta = list(filter(lambda c: __isTimeDataType(c[1]['dataType']), columnConfigs))
    valueColumnsAndMeta = list(filter(lambda c: __isNumberDataType(c[1]['dataType']), columnConfigs))

    keyColumns = list(map(lambda c: c[1]['name'], keyColumnsAndMeta))
    timeColumns = list(map(lambda c: c[1]['name'], timeColumnsAndMeta))

    timeTuples = []
    for v in valueColumnsAndMeta:
        for t in timeColumnsAndMeta:
            timeTuples.append(
                api.TimeTupleConfig(timeColumn=t[1]['name'], valueColumn=v[1]['name'])
            )
    return api.DataLoadMapping(
        keyColumns=keyColumns,
        valueModifiers=valueModifiers,
        timeColumns=timeColumns,
        frequency=None,
        valueLabelColumn=[],
        timeTuples=timeTuples
    )

def __isStringColumnType(columnType):
    return columnType == api.ColumnType.Value("String")

def __isTimeColumnType(columnType):
    return columnType == api.ColumnType.Value("Time")

def __isNumberColumnType(columnType):
    return columnType == api.ColumnType.Value("Number")

def __columnTypeToString(projectedColumn):
    if __isStringColumnType(projectedColumn.type):
        return "String"
    if __isTimeColumnType(projectedColumn.type):
        return "Time"
    if __isNumberColumnType(projectedColumn.type):
        return "Number"




#######################################
### Pandas helpers to read meta
############
def __getColumnTypeOptions(dType, name):
    if is_datetime64_any_dtype(dType):
        return {'dateFormat': 'ISO_DATE', 'dataType': 'TimeColumnConfig', 'name': name}

    if is_numeric_dtype(dType):
        return {'dataType': 'NumberColumnConfig', 'name': name}

    if is_string_dtype(dType):
        return {'dataType': 'StringColumnConfig', 'name': name}

    raise Exception(f'Unsupprted dType: {dType}')


def __getSampleRowsPandas(df):
    rowSamples = []
    for idx, row in df[0:100].iterrows():
        rowGrpc = list(map(lambda d: api.OptionalString(value=proto.StringValue(value=str(d))), row.to_list()))
        rowSamples.append(api.RowSample(values=rowGrpc))
    return rowSamples


def __getColumnSamplesPandas(df):
    columnSamples = []
    for col in df.columns:
        colvalues = list(map(lambda d: "" if d is None else str(d), df[col][0:100].tolist()))
        colGrpc = api.ColumnSample(
            columnName=col,
            values=colvalues
        )
        columnSamples.append(colGrpc)
    return columnSamples


def __getColumnConfigsPandas(df: pd.DataFrame):
    typedColumnConfigs = []
    pythonConfigs = []
    for name, dType in df.dtypes.items():
        # Compute the base type
        baseConfig = __getColumnTypeOptions(dType, name)
        pythonConfigs.append(baseConfig)

        # And make the correct grpc model
        if baseConfig['dataType'] == 'StringColumnConfig':
            typed_conf = api.ColumnConfig(stringColumnConfig=api.StringColumnConfig(
                name=name,
                displayLabel=name,
                modifier=None,
                ontology=None
            ))
            typedColumnConfigs.append(typed_conf)
        elif baseConfig['dataType'] == 'NumberColumnConfig':
            typed_conf = api.ColumnConfig(numberColumnConfig=api.NumberColumnConfig(
                name=name,
                displayLabel=name,
            ))
            typedColumnConfigs.append(typed_conf)
        elif baseConfig['dataType'] == 'TimeColumnConfig':
            typed_conf = api.ColumnConfig(timeColumnConfig=api.TimeColumnConfig(
                name=name,
                displayLabel=name,
                dateFormat=baseConfig['dateFormat']
            ))
            typedColumnConfigs.append(typed_conf)

    return list(zip(typedColumnConfigs, pythonConfigs))


def __makeLineQueryPandas(line_query):
    filterExprs = []
    # Make the filter expression from columns
    for filt in line_query.filters:
        if len(filt.stringFilter.stringFilter) > 0:
            filt_str = ' or '.join(f'{filt.stringFilter.name} == "{filtValue.value.value}"' for filtValue in filt.stringFilter.stringFilter)
            filterExprs.append(f'({filt_str})')
        elif len(filt.numberFilter.numberFilter):
            if len(filt.numberFilter.numberFilter) == 1:
                filt_num = f'{filt.numberFilter.name} == {filt.numberFilter.numberFilter[0]}'
                filterExprs.append(f'({filt_num})')
            else:
                filt_num = f'{filt.numberFilter.name} >= {filt.numberFilter.numberFilter[0]} and {filt.numberFilter.name} < {filt.numberFilter.numberFilter[1]}'
                filterExprs.append(f'({filt_num})')
        #TODO: Support time filter after server format is known
        elif type == "Time":
            pass
    return filterExprs


def getDatasourceMetaReplyPandas(df, ds_id, ds_name):
    typedColumnConfigsAndMeta = __getColumnConfigsPandas(df)
    valueModifiers = []
    data_load_mappings = __getDataLoadMappings(typedColumnConfigsAndMeta, valueModifiers)
    rowSamples = __getSampleRowsPandas(df)
    columnSamples = __getColumnSamplesPandas(df)
    return api.DataSourceMetaReply(
        dataSourceId=ds_id,
        dataSourceName=ds_name,
        columnConfigs=list(map(lambda x: x[0], typedColumnConfigsAndMeta)),
        dataLoadMapping=data_load_mappings,
        sampleData=rowSamples,  # repeated RowSample
        columnSamples=columnSamples,  # repeated ColumnSample
    )


def __dataTypeToString(dataType):
    if __isTimeDataType(dataType):
        return "Time"
    if __isNumberDataType(dataType):
        return "Number"
    if __isStringDataType(dataType):
        return "String"
    raise Exception(f'Unsupprted dataType: {dataType}')

def __tsToUnixEpochSeconds(timeStamp):
    return np.int_(timeStamp.value / 10**9)

# project_cols is a ProjectColumn[] grpc message
# Iterate a dataframe's rows as api.DataRecordsReply
# time columns must be serialized as numbers prior to this
def __serializeDataFrame(df, project_cols, chunk_size = 100):
    string_project = list(filter(lambda x: __isStringColumnType(x.type), project_cols))
    string_names = list(map(lambda x: x.name, string_project))
    string_dict = dict([(item, index) for (index, item) in enumerate(string_names)])

    number_project = list(filter(lambda x: __isNumberColumnType(x.type), project_cols))
    number_names = list(map(lambda x: x.name, number_project))
    number_dict = dict([(item, index) for (index, item) in enumerate(number_names)])

    time_project = list(filter(lambda x: __isTimeColumnType(x.type), project_cols))
    time_names = list(map(lambda x: x.name, time_project))
    time_dict = dict([(item, index) for (index, item) in enumerate(time_names)])

    num_rows = df.shape[0]
    for chunk_df in list(filter(lambda x: not x.empty, np.array_split(df, math.ceil(num_rows / chunk_size)))):
        data_records = []
        for _, row in chunk_df.iterrows():
            strings = [api.OptionalString(value=proto.StringValue(value=None))] * len(string_names)
            numbers = [api.OptionalNumber(value=proto.DoubleValue(value=None))] * len(number_names)
            times = [api.OptionalTime(value=proto.Int64Value(value=None))] * len(time_names)

            for col in project_cols:
                # Strings
                if __isStringColumnType(col.type):
                    if row[col.name] == None:
                        strings[string_dict[col.name]] = api.OptionalString(value=None)
                    else:
                        strings[string_dict[col.name]] = api.OptionalString(value=proto.StringValue(value=row[col.name]))

                # Numbers
                elif __isNumberColumnType(col.type):
                    if row[col.name] == None or math.isnan(row[col.name]):
                        numbers[number_dict[col.name]] = api.OptionalNumber(value=None)
                    else:
                        numbers[number_dict[col.name]] = api.OptionalNumber(value=proto.DoubleValue(value=row[col.name]))

                # Times
                elif __isTimeColumnType(col.type):
                    if row[col.name] == None or math.isnan(row[col.name].value):
                        times[time_dict[col.name]] = api.OptionalTime(value=None)
                    else:
                        times[time_dict[col.name]] = api.OptionalTime(value=proto.Int64Value(value=__tsToUnixEpochSeconds(row[col.name])))
            data_records.append(api.DataRecord(strings=strings, numbers=numbers, times=times))
        yield api.DataRecordsReply(records=data_records)


def dataSourceUniquesStreamPandas(df, request, chunk_size = 100):
    print("dataSourceUniquesStreamPandas", MessageToJson(request))
    df_names = list(map(lambda c:  c.name, request.projectColumns))
    stringsOnly = list(
        df[df_names].select_dtypes(include=['category', 'object']).columns
    )
    unique_df = df[df_names].drop_duplicates(subset=stringsOnly)
    # Run the serialize code
    yield from __serializeDataFrame(unique_df, request.projectColumns, chunk_size)


def dataSourceQueryStreamPandas(df, request):
    print("dataSourceQueryStreamPandas", MessageToJson(request))

    # Grab the projections we care about
    project_names = list(map(lambda x: x.name, request.projectCols))

    # Grab our string + time projections to sort byt
    string_project = list(filter(lambda x: __isStringColumnType(x.type), request.projectCols))
    string_names = list(filter(lambda x: x.name), string_project))

    time_project = list(filter(lambda x: __isTimeColumnType(x.type), request.projectCols))
    time_names = list(filter(lambda x: x.name), time_project))

    for line_query in request.lineQueries:
        # Apply the line query to filter to
        filterExprs = __makeLineQueryPandas(line_query)
        line_query = ' and '.join(filterExprs)

        # Filter data + sort by time
        line_result_df = df[project_names].query(line_query)
        line_result_df.sort_values(by=string_names + time_names, inplace=True)

        # Send our batch -- do it in 1 chunk
        num_rows = line_result_df.shape[0]
        yield from __serializeDataFrame(line_result_df, request.projectColumns, num_rows)
