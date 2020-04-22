'''
A demo usage of the data_frame_serivcer and kicking off rpc.
'''

from concurrent import futures
from dv_pyclient.grpc import datasource_manager as ds
from dv_pyclient.grpc import dataSources_pb2_grpc as rpc
from io import StringIO
import grpc
import logging
import pandas as pd

class BasicServer:
    '''
    A basic server that supports multiple data frames.
    '''

    df_map = {}

### Run the server and server your datasource
def serve(data_source_id, data_source_name, data_frame):
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    server_port = 50051

    ds_manager = ds.DataSourceManager()

    test_datasource_pd = ds.PandasDatasource(test_df_id, test_df_name, test_df)
    ds_manager.addDataSource(test_df_id, test_df_name, test_datasource_pd)

    # A John Hopkins

    rpc.add_RemoteDataSourceServicer_to_server(ds_manager, server)
    server.add_insecure_port(f'[::]:{server_port}')
    server.start()
    print(f"Started server on port {server_port}")
    server.wait_for_termination()


if __name__ == '__main__':
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

    test_df = pd.read_csv(StringIO(sample_data), sep=",", parse_dates=['date'])

    logging.basicConfig()
    serve(test_df, ds_id, ds_name)
