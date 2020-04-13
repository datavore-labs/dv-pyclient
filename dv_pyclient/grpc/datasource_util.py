from dv_pyclient.grpc import dataSources_pb2 as api
from pandas.core.dtypes.common import (
    is_string_dtype,
    is_numeric_dtype,
    is_datetime64_any_dtype,
)
import pandas as pd
import google.protobuf.wrappers_pb2 as proto
import numpy as np


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
        frequency=proto.StringValue(value=None),
        valueLabelColumn=[],
        timeTuples=timeTuples
    )


#######################################
### Pandas helpers to read meta
############
def __getColumnTypeOptions(dType, name):
    if is_numeric_dtype(dType):
        return {'dataType': 'NumberColumnConfig', 'name': name}
    elif is_string_dtype(dType):
        return {'dataType': 'StringColumnConfig', 'name': name}
    if is_datetime64_any_dtype(dType):
        return {'dateFormat': 'ISO_DATE', 'dataType': 'TimeColumnConfig', 'name': name}
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
                modifier=api.PredicateModifier.Value('None'),
                ontology=proto.StringValue(value=None)
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


def dataSourceUniquesStreamPandas(df, request):
    chunk_size = 100  # Determines the number of records per rpc batch
    columns = list(request.columns)
    unique_df = df[columns].drop_duplicates()
    for chunk_df in np.array_split(unique_df, chunk_size):
        data_records = []
        for idx, row in chunk_df.iterrows():
            strings, numbers, times = [], [], []
            for c in columns:
                col_value = row[c] if row[c] is not None else ""
                strings.append(api.OptionalString(value=proto.StringValue(value=col_value)))
            data_records.append(api.DataRecord(strings=strings, numbers=numbers, times=times))
        yield api.DataRecordsReply(records=data_records)


def dataSourceQueryStreamPandas(df, request):
    # Make and resolve the data for each line requested.
    # We yield batches of DataRecordsReply, one for each line requested
    for querystr in request.lineQueries:
        columns = []
        column_types = []
        filterExprs = []
        # Make the filter expression from columns
        for filt in querystr.columns:
            columns.append(filt.name)
            column_types.append(filt.type)
            if filt.type == api.ColumnType.Value("String") and len(filt.stringFilter) > 0:
                filt_str = ' or '.join(f'{filt.name} == "{filtValue.value.value}"' for filtValue in filt.stringFilter)
                filterExprs.append(f'({filt_str})')
            elif filt.type == api.ColumnType.Value("Number") and len(filt.numberFilter) > 0:
                if len(filt.numberFilter) == 1:
                    filt_num = f'{filt.name} == {filt.numberFilter[0].value.value}'
                    filterExprs.append(f'({filt_num})')
                else:
                    filt_num = f'{filt.name} >= {filt.numberFilter[0].value.value} and {filt.name} < {filt.numberFilter[1].value.value}'
                    filterExprs.append(f'({filt_num})')
            #TODO: Support time filter after server format is known
            elif type == "Time":
                if len(filt.timeFilter) == 1:
                    f'{filt.name} == {filt.timeFilter[0].value.value}'
                else:
                    f'{filt.name} >= {filt.timeFilter[0].value.value} and {filt.name} < {filt.timeFilter[1].value.value}'
        line_query = ' and '.join(filterExprs)

        # Filter data
        line_result_df = df[columns].query(line_query)
        # Inplace convert all date columns to unixepoch
        date_cols = list(map(lambda x: x[0],
                             filter(lambda t: t[1] == api.ColumnType.Value("Time"), list(zip(columns, column_types)))))
        for date_col in date_cols:
            line_result_df[date_col] = line_result_df[date_col].astype(np.int64)

        # TODO: Sort values by date columns
        line_result_df.sort_values(by=date_col, inplace=True)

        # Serialize
        data_records = []
        for idx, row in line_result_df.iterrows():
            strings, numbers, times = [], [], []
            for c, c_type in zip(columns, column_types):
                if c_type == api.ColumnType.Value("String"):
                    strings.append(api.OptionalString(value=proto.StringValue(value=row[c])))
                elif c_type == api.ColumnType.Value("Number"):
                    numbers.append(api.OptionalNumber(value=proto.DoubleValue(value=row[c])))
                elif c_type == api.ColumnType.Value("Time"):
                    times.append(api.OptionalTime(value=proto.Int64Value(value=row[c])))
            data_records.append(api.DataRecord(strings=strings, numbers=numbers, times=times))
        yield api.DataRecordsReply(records=data_records)
