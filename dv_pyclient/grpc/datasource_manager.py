from dv_pyclient.grpc import dataSources_pb2 as api
from dv_pyclient.grpc import dataSources_pb2_grpc as rpc
from dv_pyclient.grpc import datasource_helper as util
from google.protobuf.json_format import MessageToJson
import pandas as pd
import grpc
import copy

class Datasource:
    def dataSourceUniques(self, column_map: util.ColumnConfigs):
        pass

    def sampleDataSourceMeta(self, request: api.DataSourceMetaRequest, context) -> api.DataSourceMetaReply:
        pass

    def dataSourceQuery(self, line_query: api.LineQuery, column_map: util.ColumnConfigs):
        pass


class PandasDatasource(Datasource):
    def __init__(self, id, name, df):
        self.ds_id = id
        self.ds_name = name
        self.df = df
        self.local_projections = list(df.columns)

    def dataSourceUniques(self, column_map: util.ColumnConfigs):
        cm = copy.deepcopy(column_map)
        cm.number_dict = {}
        cm.time_dict = {}
        cm.number_cols = []
        cm.time_cols = []
        unique_df = self.df[cm.string_cols].drop_duplicates()
        yield from util.serializeDataframe(unique_df, cm)

    def sampleDataSourceMeta(self) -> api.DataSourceMetaReply:
        return util.getDatasourceMetaReplyPandas(self.df, self.ds_id, self.ds_name)

    def dataSourceQuery(self, line_query: api.LineQuery, column_map: util.ColumnConfigs):
        print("dataSourceQuery", MessageToJson(line_query))
        # Compute over local projections the columns we need for the query (request_proj intersect local_projections]
        cm = copy.deepcopy(column_map)
        project_types_cols = [[proj, col_type] for proj, col_type in zip(cm.project_cols, cm.column_types) if
                              proj in self.local_projections]
        query_projections = list(map(lambda pc: pc[0], project_types_cols))
        query_col_types = list(map(lambda pc: pc[1], project_types_cols))
        cm.project_cols = query_projections
        cm.column_types = query_col_types

        filterExprs = util.makeLineQueryPandas(line_query)
        line_query = ' and '.join(filterExprs)

        # Filter and sort data
        line_result_df = self.df[query_projections].query(line_query)
        line_result_df.sort_values(by=cm.string_cols + cm.time_cols, inplace=True)
        yield from util.serializeDataframe(line_result_df, cm, chunk_size=100)


class DataSourceManager(rpc.RemoteDataSourceServicer):

    def __init__(self):
        self.ds_manager = {}

    def addDataSource(self, id: str, name: str, ds: Datasource):
        self.ds_manager[id] = {'name': name, 'ds': ds}

    def ListDataSources(self, request: api.ListDataSourcesRequest, context) -> api.ListDataSourcesReply:
        datasources = []
        for ds_id in self.ds_manager:
            datasources.append(api.DataSourceResult(id=ds_id, name=self.ds_manager[ds_id]['name']))
        return api.ListDataSourcesReply(dataSources=datasources)

    def dataSourceQuery(self, request: api.DataSourceQueryRequest, context):
        # print("dataSourceQuery", MessageToJson(request))
        if any(map(lambda query: query.dataSourceId not in self.ds_manager.keys(), request.lineQueries)):
            context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
            context.set_details(f'Unknown dataSourceId for query. Must be: {self.ds_manager.keys()}')
            raise RuntimeError('Invalid dataSourceQuery request')

        column_map = util.getColumnMap(request.projectColumns)
        for line_query in request.lineQueries:
            ds = self.ds_manager[line_query.dataSourceId]
            yield from ds['ds'].dataSourceQuery(line_query, column_map)

    def dataSourceUniques(self, request: api.DataSourceUniquesRequest, context):
        # print("dataSourceUniques", MessageToJson(request))
        try:
            datasource: Datasource = self.ds_manager[request.dataSourceId]['ds']
        except:
            context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
            context.set_details('Invalid dataSourceUnique request, dataSourceId not found')
            raise RuntimeError('Invalid dataSourceUnique request, dataSourceId not found')

        column_map = util.getColumnMap(request.projectColumns)
        yield from datasource.dataSourceUniques(column_map)

    def sampleDataSourceMeta(self, request: api.DataSourceMetaRequest, context) -> api.DataSourceMetaReply:
        # print("sampleDataSourceMeta", MessageToJson(request))
        try:
            datasource: Datasource = self.ds_manager[request.dataSourceId]['ds']
        except:
            context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
            context.set_details('Invalid sampleDataSourceMeta request, dataSourceId not found')
            raise RuntimeError('Invalid sampleDataSourceMeta request, dataSourceId not found')

        result = datasource.sampleDataSourceMeta()
        context.set_code(grpc.StatusCode.OK)
        return result
