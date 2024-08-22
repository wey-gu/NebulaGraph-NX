# SPDX-License-Identifier: Apache-2.0
# Copyright 2023 The NebulaGraph Authors. All rights reserved.

from typing import Dict, List

import networkx as nx
from nebula3.mclient import MetaCache, HostAddr
from nebula3.sclient.GraphStorageClient import GraphStorageClient

from ng_nx.utils import NebulaGraphConfig, cast


class NebulaScanReader:
    def __init__(
        self,
        edges: List[str],
        properties: List[List[str]],
        nebula_config: NebulaGraphConfig,
        limit: int,
        with_rank: bool = False,  # this enable the multi-graph, and the edge_key is "__rank__"
    ):
        self.edges = edges
        self.properties = properties
        self.limit = limit
        self.space = nebula_config.space

        metad_hosts = nebula_config.metad_hosts.split(",")
        metad_host_list = [
            (host.split(":")[0], int(host.split(":")[1])) for host in metad_hosts
        ]
        self.meta_cache = MetaCache(metad_host_list, 50000)
        self.graph_storage_client = GraphStorageClient(self.meta_cache)

        self.with_rank = with_rank

        assert len(edges) > 0 and len(edges) == len(
            properties
        ), "edges and properties should have the same length"

    def read(self) -> nx.MultiDiGraph:
        g = nx.MultiDiGraph()

        for i, edge in enumerate(self.edges):
            edge_properties = self.properties[i]
            resp = self.graph_storage_client.scan_edge(
                space_name=self.space, edge_name=edge
            )
            edge_count = 0
            while resp.has_next() and edge_count < self.limit:
                result = resp.next()
                for edge_data in result.as_relationships():
                    src = cast(edge_data.start_vertex_id())
                    dst = cast(edge_data.end_vertex_id())
                    props = {}
                    for prop in edge_properties:
                        props[prop] = cast(edge_data.properties().get(prop))
                    if self.with_rank:
                        rank = edge_data.ranking()
                        props["__rank__"] = rank
                        g.add_edge(src, dst, key=rank, **props)
                    else:
                        g.add_edge(src, dst, **props)
                    edge_count += 1
                    if edge_count >= self.limit:
                        break

        return g

    def release(self):
        self.graph_storage_client.close()

    def __del__(self):
        self.release()
