from dv_pyclient.grpc.datavore import dataSources_pb2 as api
from dv_pyclient.grpc.datavore import dataSources_pb2_grpc as rpc
import grpc
import google.protobuf.wrappers_pb2 as proto


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

def dataSourceQuery(stub):
    source_cols = ["date", "trans", "symbol", "qty", "currency"]
    column_types = ["Time", "String", "String", "Number", "String"]
    filters = [[], ["BUY"], ["RHAT"], [], [], ["USD"]]
    query_columns = []
    for col, type, filter in zip(source_cols, column_types, filters):
        stringFilter, numberFilter, timeFilter = [], [], []
        if type == "String":
            stringFilter = list(map(lambda f: api.OptionalString(value=proto.StringValue(value=f)), filter))
        if type == "Number":
            numberFilter = list(map(lambda f: api.OptionalNumber(value=proto.DoubleValue(value=f)), filter))
        if type == "Time":
            timeFilter = list(map(lambda f: api.OptionalTime(value=proto.Int64Value(value=f)), filter))

        query_columns.append(
            api.QueryColumn(
                name=col,
                type=type,
                stringFilter=stringFilter,
                numberFilter=numberFilter,
                timeFilter=timeFilter
            )
        )
    line_query = api.LineQuery(columns=query_columns)
    request = api.DataSourceQueryRequest(
        lineQueries=[line_query]
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
    sampleDataSourceMeta(rpc_stub, ds_id="ds_id_test_grpc")
    try:
        sampleDataSourceMeta(rpc_stub, ds_id="ds_id_test")
    except grpc._channel._InactiveRpcError as rpcErr:
        print(f"Got error {rpcErr}")

    ## datasource uniques
    dataSourceUniques(rpc_stub)

    dataSourceQuery(rpc_stub)


if __name__ == '__main__':
    run_main()
