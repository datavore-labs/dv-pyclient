from dv_pyclient.grpc.datavore import dataSources_pb2 as api
from dv_pyclient.grpc.datavore import dataSources_pb2_grpc as rpc
import grpc


def listRequest(stub):
    ds_list = stub.ListDataSources(request=api.ListDataSourcesRequest())
    print(ds_list)

def sampleDataSourceMeta(stub, ds_id):
    meta = stub.sampleDataSourceMeta(request=api.DataSourceMetaRequest(dataSourceId=ds_id))
    print(meta)

def dataSourceUniques(stub):
    request = api.DataSourceUniquesRequest(dataSourceId="ds_id_test_grpc", columns=['trans', 'symbol', 'currency'])
    res = stub.dataSourceUniques(request=request)
    for batch in res:
        print(batch)

def dataSourceQuery():
    request = api.DataSourceQueryRequest()
    # message QueryColumn {
    #     string name = 1;
    # ColumnType type = 2;
    # }
    # message DataSourceQueryRequest {
    #     repeated QueryColumn queryColumns = 1;
    # repeated LineDefinition lines = 2;
    # }
    # message LineDefinition {
    #     // Data predicates
    #     repeated string keyPredicateIds = 1;
    #     repeated OptionalString keyPath = 2; // Option[String]
    #     string timePredicateId = 3;
    #     string valuePredicateId = 4;
    #     google.protobuf.StringValue frequency = 5; // Option[String]
    #     string dataSourceId = 6;
    # }


if __name__ == '__main__':
    ## Setup channel
    channel = grpc.insecure_channel('localhost:50051')
    rpc_stub = rpc.RemoteDataSourceStub(channel)

       ## List datasources request
    listRequest(rpc_stub)

    # Sample datasource meta request
    sampleDataSourceMeta(rpc_stub, ds_id="ds_id_test_grpc")
    try:
        sampleDataSourceMeta(rpc_stub, ds_id="ds_id_test")
    except grpc._channel._InactiveRpcError as rpcErr:
        print(f"Got error {rpcErr}")

    ## datasource uniques
    dataSourceUniques(rpc_stub)

