'''
A basic data frame backed servicer implementing the gRPC spec.

Exposes an easy eay to register data frames with an id and name.
'''

import sys
import grpc
import dv_pyclient.grpc.dataframe_utils as grpc_dataframe
from typing import Generator
from google.protobuf.json_format import MessageToJson
from dv_pyclient.grpc import dataSources_pb2 as msg
from dv_pyclient.grpc.dataSources_pb2_grpc import RemoteDataSourceServicer

# LOGGING - @todo: figure this out better
import logging
logging.basicConfig(
    format='[%(asctime)s] {%(filename)s:%(lineno)d} %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class DataFrameServicer(RemoteDataSourceServicer):
    '''
    A data frame backed servicer.
    '''
    def __init__(self):
        # { remote_data_id: { id, name, df } }
        self.registry = {}

    def upsert_data_frame(self, id, name, df):
        '''
        Registers df to the given id

        :param id: String - The remote data id -- unique to this server, self provided
        :param name: String - The remote data name
        :param df: String - data frame to back the remote id
        '''
        if id in self.registry:
            logger.info(f'Updating id {id}')
            if (self.registry[id]['name'] != name):
                logger.warn(f'Unexpected name change when updating. From {self.registry[id]["name"] != name} to {name}. This might be an error!')

        self.registry[id] = {
            'id': id,
            'name': name,
            'df': df
        }

        logger.info(f'Upsert {name} @ {id}')

    # gRPC interface implementations
    def ListDataSources(self, request: msg.ListDataSourcesRequest, context) -> msg.ListDataSourcesReply:
        '''
        Return a list of dataSources this remote service has
        '''
        try:
            # Build output by for comprehension over registry
            logger.info(f'ListDataSources: {MessageToJson(request)}')
            output = [
                msg.DataSourceResult(id = source['id'], name = source['name'])
                # Sort the registry by name
                for source in sorted(self.registry.values(), key = lambda x: x['name'])
            ]
            return msg.ListDataSourcesReply(dataSources=output)
        except Exception as e:
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details('Internal server error.')
            logger.exception(f'Failed to list data sources: {str(e)}.')
            raise e

    def dataSourceUniques(self, request: msg.DataSourceUniquesRequest, context) -> Generator[msg.DataRecordsReply, None, None]:
        '''
        Return unique records for indexing into search
        '''
        try:
            logger.info(f'dataSourceUniques: {MessageToJson(request)}')

            if not request.dataSourceId in self.registry:
                raise KeyError(f'Requested remote id {request.dataSourceId} not in registry.')

            df = self.registry[request.dataSourceId]['df']
            yield from grpc_dataframe.generate_data_frame_uniques(df, request)
        except Exception as e:
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details('Internal server error.')
            logger.exception(f'Failed to get uniques: {str(e)}.')
            raise e

    def sampleDataSourceMeta(self, request: msg.DataSourceMetaRequest, context) -> msg.DataSourceMetaReply:
        '''
        Returns the meta needed to read the dataRecords as lines
        '''
        try:
            logger.info(f'sampleDataSourceMeta: {MessageToJson(request)}')
            if not request.dataSourceId in self.registry:
                raise KeyError(f'Requested remote id {request.dataSourceId} not in registry.')

            registered = self.registry[request.dataSourceId]
            df = registered['df']
            name = registered['name']
            return grpc_dataframe.generate_data_frame_meta(df, name, request)
        except Exception as e:
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details('Internal server error.')
            logger.exception(f'Failed to sample data: {str(e)}.')
            raise e

    def dataSourceQuery(self, request: msg.DataSourceQueryRequest, context) -> Generator[msg.DataRecordsReply, None, None]:
        '''
        Sends a list of lines to retrieve, and gets the dataRecords back
        '''
        try:
            logger.info(f'dataSourceQuery: {MessageToJson(request)}')

            for query in request.lineQueries:
                if not query.dataSourceId in self.registry:
                    raise KeyError(f'Requested remote id {query.dataSourceId} not in registry.')

                registered = self.registry[query.dataSourceId]
                df = registered['df']
                name = registered['name']
                sub_request = msg.DataSourceQueryRequest(
                    projectColumns = request.projectColumns,
                    lineQueries = [query]
                )
                yield from grpc_dataframe.query_data_frame(df, sub_request)
        except Exception as e:
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details('Internal server error.')
            logger.exception(f'Failed to query data: {str(e)}.')
            raise e
