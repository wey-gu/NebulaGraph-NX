# nebulagraph --> networkX

## 从 NebulaGraph 中获得一张图，存储为 pd dataframe

from nebula3.gclient.net import ConnectionPool
from nebula3.Config import Config
import pandas as pd
from typing import Dict
from nebula3.data.ResultSet import ResultSet

## 从 pd dataframe 中获得一张图，存储为 networkX

import networkx as nx

G = nx.from_pandas_edgelist(df, 'src', 'dst', 'weight', create_using=nx.DiGraph())


## 在 G 中跑一个图算法，pagerank

pr = nx.pagerank(G, alpha=0.85, max_iter=100, tol=1e-06, weight='weight', dangling=None)

## 设计 ngnx(nebulagraph-netowrkx) 的 API

"""
from ngnx import ngnx_query_reader
from networkx import nx

nebula_config = {
    "graphd": "nebula2",
    "port": 9669,
    "user": "root",
    "password": "nebula"
}

reader = ngnx_query_reader(space="basketballplayer", edges=["follow"], properties=[["degree"]], nebula_config=nebula_config, limit=100)

g = reader.read()

# call pagerank on g
pr = nx.pagerank(g, alpha=0.85, max_iter=100, tol=1e-06, weight='weight', dangling=None)
"""

# class ngnx_query_reader:

class ngnx_query_reader:
    def __init__(self, space: str, edges: list, properties: list, nebula_config: dict, limit: int, ):
        self.space = space
        self.edges = edges
        self.properties = properties
        self.limit = limit
        self.nebula_config = nebula_config

        # define a config
        config = Config()

        # init connection pool
        self.connection_pool = ConnectionPool()
        assert self.connection_pool.init([(nebula_config.get("graphd", "127.0.0.1"), nebula_config.get("port", 9669))], config), "Init Connection Pool Failed"
        assert len(edges) > 0 and len(edges) == len(properties), "edges and properties should have the same length"

    @staticmethod
    def result_to_df(result: ResultSet) -> pd.DataFrame:
        """
        build list for each column, and transform to dataframe
        """
        assert result.is_succeeded()
        columns = result.keys()
        d: Dict[str, list] = {}
        for col_num in range(result.col_size()):
            col_name = columns[col_num]
            col_list = result.column_values(col_name)
            d[col_name] = [x.cast() for x in col_list]
        return pd.DataFrame(d)

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
                df = df.append(self.result_to_df(result))
            # build graph
            return nx.from_pandas_edgelist(df, 'src', 'dst', self.properties[0], create_using=nx.DiGraph())

    def release(self):
        self.connection_pool.close()