from dv_pyclient.grpc import datasource_manager as ds
from dv_pyclient.grpc import dataSources_pb2_grpc as rpc
import pandas as pd
from io import StringIO
from concurrent import futures
import logging
import grpc


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

### Run the server and server your datasource
def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    server_port = 50051

    ds_manager = ds.DataSourceManager()

    # A test pandas datasource
    test_df = pd.read_csv(StringIO(sample_data), sep=",", parse_dates=['date'])
    test_df_id = "my_assigned_ds_id"
    test_df_name = "my_stock_trans"
    test_datasource_pd = ds.PandasDatasource(test_df_id, test_df_name, test_df)
    ds_manager.addDataSource(test_df_id, test_df_name, test_datasource_pd)

    # A John Hopkins

    rpc.add_RemoteDataSourceServicer_to_server(ds_manager, server)
    server.add_insecure_port(f'[::]:{server_port}')
    server.start()
    print(f"Started server on port {server_port}")
    server.wait_for_termination()


if __name__ == '__main__':
    logging.basicConfig()
    serve()
