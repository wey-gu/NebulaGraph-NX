# SPDX-License-Identifier: Apache-2.0
# Copyright 2024 The NebulaGraph Authors. All rights reserved.

import networkx as nx
import pandas as pd
from nebula3.Config import Config
from nebula3.gclient.net import ConnectionPool
from nebula3.data.ResultSet import ResultSet

from ng_nx.utils import NebulaGraphConfig, result_to_df


class NebulaReader:
    def __init__(
        self,
        edges: list,
        properties: list,
        nebula_config: NebulaGraphConfig,
        limit: int,
    ):
        self.edges = edges
        self.properties = properties
        self.limit = limit

        config = Config()
        graphd_hosts = nebula_config.graphd_hosts.split(",")
        graphd_host_list = [
            (host.split(":")[0], int(host.split(":")[1])) for host in graphd_hosts
        ]
        self.space = nebula_config.space
        self.nebula_user = nebula_config.user
        self.nebula_password = nebula_config.password
        self.connection_pool = ConnectionPool()
        assert self.connection_pool.init(
            graphd_host_list, config
        ), "Init Connection Pool Failed"
        assert len(edges) > 0 and len(edges) == len(
            properties
        ), "edges and properties should have the same length"

    def read(self):
        with self.connection_pool.session_context(
            self.nebula_user, self.nebula_password
        ) as session:
            assert session.execute(
                f"USE {self.space}"
            ).is_succeeded(), f"Failed to use space {self.space}"
            result_list = []
            g = nx.MultiDiGraph()
            for i in range(len(self.edges)):
                edge = self.edges[i]
                properties = self.properties[i]
                properties_query_field = ""
                for property in properties:
                    properties_query_field += f", e.{property} AS {property}"
                result = session.execute(
                    f"MATCH ()-[e:`{edge}`]->() RETURN src(e) AS src, dst(e) AS dst{properties_query_field} LIMIT {self.limit}"
                )
                # print(f'query: MATCH ()-[e:`{edge}`]->() RETURN src(e) AS src, dst(e) AS dst{properties_query_field} LIMIT {self.limit}')
                # print(f"Result: {result}")
                assert result.is_succeeded()
                result_list.append(result)

            # merge all result
            for i, result in enumerate(result_list):
                _df = result_to_df(result)
                # TBD, consider add label of edge
                properties = self.properties[i] if self.properties[i] else None
                _g = nx.from_pandas_edgelist(
                    _df, "src", "dst", properties, create_using=nx.MultiDiGraph()
                )
                g = nx.compose(g, _g)
            return g

    def release(self):
        self.connection_pool.close()

    def __del__(self):
        self.release()

class NebulaQueryReader:
    def __init__(self, nebula_config: NebulaGraphConfig):
        self.config = nebula_config
        self.connection_pool = ConnectionPool()
        graphd_hosts = nebula_config.graphd_hosts.split(",")
        graphd_host_list = [
            (host.split(":")[0], int(host.split(":")[1])) for host in graphd_hosts
        ]
        config = Config()
        assert self.connection_pool.init(
            graphd_host_list, config
        ), "Init Connection Pool Failed"

    def read(self, query: str) -> nx.MultiDiGraph:
        with self.connection_pool.session_context(
            self.config.user, self.config.password
        ) as session:
            assert session.execute(
                f"USE {self.config.space}"
            ).is_succeeded(), f"Failed to use space {self.config.space}"
            
            result: ResultSet = session.execute(query)
            assert result.is_succeeded(), f"Query execution failed: {result.error_msg()}"
            
            vis_data = result.dict_for_vis()
            return self._construct_graph(vis_data)

    def _construct_graph(self, vis_data: dict) -> nx.MultiDiGraph:
        g = nx.MultiDiGraph()
        
        # Add nodes
        for node_data in vis_data['nodes']:
            g.add_node(node_data['id'], **node_data['props'], labels=node_data['labels'])
        
        # Add edges
        for edge_data in vis_data['edges']:
            g.add_edge(
                edge_data['src'],
                edge_data['dst'],
                key=edge_data['name'],
                **edge_data['props']
            )
        
        return g

    def release(self):
        self.connection_pool.close()

    def __del__(self):
        self.release()