from concurrent import futures
import logging
import grpc

from dv_pyclient.grpc import dataSources_pb2_grpc as rpc


def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))

    ##TODO: Instantiate your class that implements rpc.RemoteDataSourceServicer
    ds_server_class = None

    rpc.add_RemoteDataSourceServicer_to_server(ds_server_class, server)
    server.add_insecure_port('[::]:50051')
    server.start()
    server.wait_for_termination()


if __name__ == '__main__':
    logging.basicConfig()
    serve()
