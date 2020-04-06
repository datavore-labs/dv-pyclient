from .datavore import dataSources_pb2 as api
from .datavore import dataSources_pb2_grpc as rpc


class RemoteDatasource(rpc.RemoteDataSourceServicer):

    def ListDataSources(self, request: api.ListDataSourcesRequest, context) -> api.ListDataSourcesReply:
        datasources = []
        for id, name in [("ds_id_a", "DS A"), ("ds_id_b", "DS B"), ("ds_id_c", "DS C")]:
            datasources.append(api.DataSourceResult(id=id, name=name))
        return api.ListDataSourcesReply(dataSources=datasources)

    def dataSourceMeta(self, request: api.DataSourceMetaRequest, context) -> api.DataSourceMetaReply:
        ds_id = request.dataSourceId
        timeTuples = [api.TimeTupleConfig(timeColumn="t1", valueColumn="v1"),
                      api.TimeTupleConfig(timeColumn="t2", valueColumn="v2")]
        dataLoadMapping = api.DataLoadMapping(
            keyColumns=["a", "b", "c"], valueModifiers=["vm"], timeColumns=["t"], frequency=None,
            valueLabelColumn=["vl"], timeTuples=timeTuples
        )
        return api.DataSourceMetaReply(
            dataSourceId=ds_id,
            dataSourceName="Fill in here",
            columnConfigs=[],
            dataLoadMapping=dataLoadMapping
        )

    def dataSourceUniques(self, request: api.DataSourceUniquesRequest, context) -> api.DataRecordsReply:
        pass

    def dataSourceQuery(self, request: api.DataSourceQueryRequest, context) -> api.DataRecordsReply:
        pass
