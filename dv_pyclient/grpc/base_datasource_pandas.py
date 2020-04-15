from dv_pyclient.grpc import dataSources_pb2 as api
from dv_pyclient.grpc import dataSources_pb2_grpc as rpc
from dv_pyclient.grpc import datasource_util as util
import grpc


class BaseDatasourcePandas(rpc.RemoteDataSourceServicer):

    def __init__(self):
        super()

    def ListDataSources(self, request: api.ListDataSourcesRequest, context) -> api.ListDataSourcesReply:
        datasources = [api.DataSourceResult(id=self.ds_id, name=self.ds_name)]
        return api.ListDataSourcesReply(dataSources=datasources)

    def dataSourceQuery(self, request: api.DataSourceQueryRequest, context):
        line_queries = request.lineQueries
        if len(line_queries) == 0:
            context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
            context.set_details(f'No lines specified in request')
            raise RuntimeError('Invalid dataSourceQuery request')

        if any(map(lambda query: query.dataSourceId != self.ds_id, request.lineQueries)):
            context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
            context.set_details(f'Unknown dataSourceId for query. Must be: {self.ds_id}')
            raise RuntimeError('Invalid dataSourceQuery request')

        yield from util.dataSourceQueryStreamPandas(self.df, request)

    def dataSourceUniques(self, request: api.DataSourceUniquesRequest, context):
        if request.dataSourceId != self.ds_id:
            context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
            context.set_details(f'Datasource id does not equal requested id: {request.dataSourceId}')
            raise RuntimeError('Invalid dataSourceUnique request')
        yield from util.dataSourceUniquesStreamPandas(self.df, request)

    def sampleDataSourceMeta(self, request: api.DataSourceMetaRequest, context) -> api.DataSourceMetaReply:
        if request.dataSourceId != self.ds_id:
            context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
            context.set_details(f'Datasource id does not equal requested id: {request.dataSourceId}')
            raise RuntimeError('Invalid sampleDataSourceMeta request')

        reply = util.getDatasourceMetaReplyPandas(self.df, self.ds_id, self.ds_name)
        context.set_code(grpc.StatusCode.OK)
        return reply
