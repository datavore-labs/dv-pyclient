from concurrent import futures
import logging
import grpc

from dv_pyclient.grpc.datavore import dataSources_pb2_grpc as rpc
from dv_pyclient.grpc import test_datasource_server as ds


def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))

    rpc.add_RemoteDataSourceServicer_to_server(ds.TestDatasource(), server)
    server.add_insecure_port('[::]:50051')
    server.start()
    server.wait_for_termination()


if __name__ == '__main__':
    logging.basicConfig()
    serve()
