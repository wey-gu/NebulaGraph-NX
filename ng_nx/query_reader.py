# SPDX-License-Identifier: Apache-2.0
# Copyright 2023 The NebulaGraph Authors. All rights reserved.

from ng_nx import NebulaGraphConfig
from ng_nx.utils import result_to_df
from nebula3.gclient.net import ConnectionPool
from nebula3.Config import Config
import pandas as pd

import networkx as nx

class NebulaReader:
    def __init__(self, space: str, edges: list, properties: list, nebula_config: NebulaGraphConfig, limit: int, ):
        self.space = space
        self.edges = edges
        self.properties = properties
        self.limit = limit
        self.nebula_config = nebula_config

        config = Config()

        self.connection_pool = ConnectionPool()
        assert self.connection_pool.init([(nebula_config.get("graphd", "127.0.0.1"), nebula_config.get("port", 9669))], config), "Init Connection Pool Failed"
        assert len(edges) > 0 and len(edges) == len(properties), "edges and properties should have the same length"

    def read(self):
        with self.connection_pool.session_context('root', 'nebula') as session:
            session.execute(f'USE {self.space}')
            assert session.execute(f'USE {self.space}').is_succeeded()
            result_list = []
            for i in range(len(self.edges)):
                edge = self.edges[i]
                properties = self.properties[i]
                properties_query_field = ""
                for property in properties:
                    properties_query_field += f", e.{property} AS {property}"
                result = session.execute(f'MATCH ()-[e:`{edge}`]->() RETURN src(e) AS src, dst(e) AS dst{properties_query_field} LIMIT {self.limit}')
                print(f'query: MATCH ()-[e:`{edge}`]->() RETURN src(e) AS src, dst(e) AS dst{properties_query_field} LIMIT {self.limit}')
                print(f"Result: {result}")
                assert result.is_succeeded()
                result_list.append(result)
            # merge all result
            df = pd.DataFrame()
            for result in result_list:
                df = df.append(result_to_df(result))
            # build graph
            return nx.from_pandas_edgelist(df, 'src', 'dst', self.properties[0], create_using=nx.DiGraph())

    def release(self):
        self.connection_pool.close()
