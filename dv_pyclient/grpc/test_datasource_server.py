from dv_pyclient.grpc.datavore import dataSources_pb2 as api
from dv_pyclient.grpc.datavore import dataSources_pb2_grpc as rpc
from dv_pyclient.grpc import datasource_util as util
import grpc
from io import StringIO
import pandas as pd
import numpy as np
import google.protobuf.wrappers_pb2 as proto

# Some import parameters
ds_id = "ds_id_test_grpc"
ds_name = "Test Datasource (grpc)"

sample_data = """
date,trans,symbol,qty,price,currency
2006-01-01,BUY,RHAT,100,35.00,USD
2006-02-01,BUY,RHAT,200,32.00,USD
2006-03-01,BUY,RHAT,300,34.00,USD
2006-04-01,BUY,RHAT,400,35.10,USD
2006-05-01,BUY,RHAT,500,35.20,USD
2006-06-01,BUY,RHAT,600,35.30,USD
2006-01-02,SELL,RHAT,100,35.60,USD
2006-02-02,SELL,RHAT,200,32.60,USD
2006-03-02,SELL,RHAT,300,34.60,USD
2006-04-02,SELL,RHAT,400,35.60,USD
2006-05-02,SELL,RHAT,500,35.60,USD
2006-06-02,SELL,RHAT,600,35.60,USD
2006-01-01,BUY,MSFT,1100,135.00,USD
2006-02-01,BUY,MSFT,1200,132.00,USD
2006-03-01,BUY,MSFT,1300,134.00,USD
2006-04-01,BUY,MSFT,1400,135.10,USD
2006-05-01,BUY,MSFT,1500,135.20,USD
2006-06-01,BUY,MSFT,1600,135.30,USD
2006-01-02,SELL,MSFT,1100,135.60,USD
2006-02-02,SELL,MSFT,1200,132.60,USD
2006-03-02,SELL,MSFT,1300,134.60,USD
2006-04-02,SELL,MSFT,1400,135.60,USD
2006-05-02,SELL,MSFT,1500,135.60,USD
2006-06-02,SELL,MSFT,1600,135.60,USD
"""

class TestDatasource(rpc.RemoteDataSourceServicer):

    def __init__(self):
        super()
        self.df = pd.read_csv(StringIO(sample_data), sep=",", parse_dates=['date'])

    def ListDataSources(self, request: api.ListDataSourcesRequest, context) -> api.ListDataSourcesReply:
        datasources = [api.DataSourceResult(id=ds_id, name=ds_name)]
        return api.ListDataSourcesReply(dataSources=datasources)

    def dataSourceQuery(self, request: api.DataSourceQueryRequest, context) -> api.DataRecordsReply:
        pass

    def dataSourceUniques(self, request: api.DataSourceUniquesRequest, context):
        if request.dataSourceId != ds_id:
            context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
            context.set_details(f'Datasource id does not equal requested id: {request.dataSourceId}')
            raise RuntimeError('Invalid datasource request')

        chunk_size = 100
        columns = list(request.columns)
        unique_df = self.df[columns].drop_duplicates()
        for chunk_df in np.array_split(unique_df, chunk_size):
            data_records = []
            for idx, row in chunk_df.iterrows():
                strings, numbers, times = [], [], []
                for c in columns:
                    col_value = row[c] if row[c] is not None else ""
                    strings.append(api.OptionalString(value=proto.StringValue(value=col_value)))
                data_records.append(api.DataRecord(strings=strings, numbers=numbers, times=[]))
            yield api.DataRecordsReply(records=data_records)

    def sampleDataSourceMeta(self, request: api.DataSourceMetaRequest, context) -> api.DataSourceMetaReply:
        if request.dataSourceId != ds_id:
            context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
            context.set_details(f'Datasource id does not equal requested id: {request.dataSourceId}')
            raise RuntimeError('Invalid datasource request')

        reply = util.getDatasourceMetaReplyPandas(self.df, ds_id, ds_name)
        context.set_code(grpc.StatusCode.OK)
        return reply
