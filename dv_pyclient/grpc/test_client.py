from dv_pyclient.grpc import dataSources_pb2 as api
from dv_pyclient.grpc import dataSources_pb2_grpc as rpc
import grpc
import google.protobuf.wrappers_pb2 as proto

ds_id = "my_assigned_ds_id"


def listRequest(stub):
    ds_list = stub.ListDataSources(request=api.ListDataSourcesRequest())
    print(ds_list)


def sampleDataSourceMeta(stub, ds_id):
    meta = stub.sampleDataSourceMeta(request=api.DataSourceMetaRequest(dataSourceId=ds_id))
    print(meta)


def dataSourceUniques(stub):
    request = api.DataSourceUniquesRequest(dataSourceId=ds_id, columns=['trans', 'symbol', 'currency'])
    res = stub.dataSourceUniques(request=request)
    for batch in res:
        print(batch)


def dataSourceQuery(stub):
    project_cols = ["date", "trans", "symbol", "qty", "price","currency"]
    column_types = ["Time", "String", "String", "Number", "Number", "String"]
    l1_filters = [
        {
            "col": "trans",
            "filter": list(map(lambda f: api.OptionalString(value=proto.StringValue(value=str(f))), ["BUY"]))
        },
        {
            "col": "symbol",
            "filter": list(map(lambda f: api.OptionalString(value=proto.StringValue(value=str(f))), ["RHAT"]))
        },
        {
            "col": "currency", "type": "String",
            "filter": list(map(lambda f: api.OptionalString(value=proto.StringValue(value=str(f))), ["USD"]))
        },
    ]
    pc = list(map(lambda c: api.ProjectColumn(name=c[0], type=api.ColumnType.Value(c[1])), zip(project_cols, column_types)))
    l1fs = list(map(lambda c: api.QueryFilter(stringFilter=api.StringFilter(name=c['col'], stringFilter=c['filter'])), l1_filters))
    l1q = api.LineQuery(filters=l1fs)
    request = api.DataSourceQueryRequest(
        projectColumns=pc,
        lineQueries=[l1q]
    )
    res = stub.dataSourceQuery(request)
    for batch in res:
        print(batch)



def run_main():
    ## Setup channel
    channel = grpc.insecure_channel('localhost:50051')
    rpc_stub = rpc.RemoteDataSourceStub(channel)

    # List datasources request
    listRequest(rpc_stub)

    # Sample datasource meta request
    sampleDataSourceMeta(rpc_stub, ds_id=ds_id)
    # try:
    #     sampleDataSourceMeta(rpc_stub, ds_id=f'garbage id must fail')
    # except grpc._channel._InactiveRpcError as rpcErr:
    #     print(f"Got error {rpcErr}")

    ## datasource uniques
    dataSourceUniques(rpc_stub)

    ## query
    dataSourceQuery(rpc_stub)


if __name__ == '__main__':
    run_main()
