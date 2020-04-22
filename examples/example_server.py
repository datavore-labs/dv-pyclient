'''
A demo usage of the data_frame_serivcer and kicking off rpc.
'''

import sys
import logging

# LOGGING
logging.basicConfig(
    format='[%(asctime)s] {%(filename)s:%(lineno)d} %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# Error handler to stderr
handler = logging.StreamHandler(sys.stderr)
handler.setLevel(logging.ERROR)
logger.addHandler(handler)

# Debug handler to stdout
handler = logging.StreamHandler(sys.stdout)
handler.setLevel(logging.DEBUG)
logger.addHandler(handler)

# Include our local libs depending on cwd
sys.path.insert(0,'.')

import grpc
import pandas as pd
from concurrent import futures
from io import StringIO
import dv_pyclient
from dv_pyclient.server.data_frame_servicer import DataFrameServicer
import dv_pyclient.grpc.dataSources_pb2_grpc as rpc

### Run the server and server your datasource
def serve(data_id, data_name, data_frame):
    # build the grpc server
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    server_port = 50051

    # Build a DataFrameServicer
    servicer = DataFrameServicer()

    # Register the served data source
    servicer.upsert_data_frame(data_id, data_name, data_frame)

    # Add the servicer to the RPC server
    rpc.add_RemoteDataSourceServicer_to_server(servicer, server)
    server.add_insecure_port(f'[::]:{server_port}')
    server.start()

    logger.info(f"Started server on port {server_port}")
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
    serve(ds_id, ds_name, test_df)
