# SPDX-License-Identifier: Apache-2.0
# Copyright 2023 The NebulaGraph Authors. All rights reserved.

from typing import Generator, List

from nebula3.Config import Config
from nebula3.gclient.net import ConnectionPool

from ng_nx.utils import NebulaGraphConfig, result_to_df


class NebulaWriter:
    def __init__(self, data: dict, nebula_config: NebulaGraphConfig):
        self.data = data
        self.label = None
        self.properties = []
        self.batch_size = None
        self.write_mode = None
        self.sink = None

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

    def set_options(
        self,
        label: str,
        properties: List[str],
        batch_size: int = 256,
        write_mode: str = "insert",
        sink: str = "nebulagraph_vertex",
    ):
        self.label = label
        self.properties = properties
        self.batch_size = batch_size
        self.write_mode = write_mode.lower()
        self.sink = sink.lower()

    def write(self):
        if self.write_mode == "update":
            raise NotImplementedError("Update mode is not implemented yet")
        if self.sink == "nebulagraph_edge":
            raise NotImplementedError("Edge sink is not implemented yet")
        if self.write_mode != "insert" or self.sink != "nebulagraph_vertex":
            raise ValueError("Only insert mode and vertex sink are supported now")
        # TODO: add more write modes and sinks later
        with self.connection_pool.session_context(
            self.nebula_user, self.nebula_password
        ) as session:
            assert session.execute(
                f"USE {self.space}"
            ).is_succeeded(), f"Failed to use space {self.space}"
            # get types of properties
            properties_types = {}
            query = f"DESC TAG {self.label}"
            result = session.execute(query)
            assert result.is_succeeded(), (
                f"Failed to get types of properties: {result.error_msg()}, "
                f"consider creating TAG {self.label} first."
            )
            types_df = result_to_df(result)

            for i in range(len(types_df)):
                properties_types[types_df.iloc[i, 0]] = types_df.iloc[i, 1]
            for property in self.properties:
                if property not in properties_types:
                    raise ValueError(
                        f"Property {property} is not defined in TAG {self.label}"
                    )

            # Set up the write query in batches, string value should be enclosed by double quotes
            # INSERT VERTEX {label} ({properties}) VALUES
            # "{vid}":({value0, value1}),...;
            query_prefix = (
                f"INSERT VERTEX {self.label} ({','.join(self.properties)}) VALUES "
            )
            query = query_prefix
            # now self.data is a dict or a generator object, key is vid, value is a list of properties or single property
            quote = '"'
            if isinstance(self.data, dict):
                for i, (vid, properties) in enumerate(self.data.items()):
                    if i % self.batch_size == 0 and i != 0:
                        # execute the query
                        # remove tailing comma
                        query = query[:-1]
                        result = session.execute(query)
                        assert (
                            result.is_succeeded()
                        ), f"Failed to write data: {result.error_msg()}"
                        # reset the query
                        query = query_prefix
                    if isinstance(properties, list):
                        # should add quotes to string values
                        query += f"{quote}{vid}{quote}:({','.join([quote+str(value)+quote if properties_types[self.properties[i]] == 'string' else str(value) for i, value in enumerate(properties)])}),"
                    else:
                        query += f"{quote}{vid}{quote}:({quote+str(properties)+quote if properties_types[self.properties[0]] == 'string' else str(properties)}),"
                # execute the last query
                query = query[:-1]
                result = session.execute(query)
                assert (
                    result.is_succeeded()
                ), f"Failed to write data: {result.error_msg()}"
            elif isinstance(self.data, Generator):
                for i, (vid, properties) in enumerate(self.data):
                    if i % self.batch_size == 0 and i != 0:
                        # execute the query
                        # remove tailing comma
                        query = query[:-1]
                        result = session.execute(query)
                        assert (
                            result.is_succeeded()
                        ), f"Failed to write data: {result.error_msg()}"
                        # reset the query
                        query = query_prefix
                    if isinstance(properties, list):
                        # should add quotes to string values
                        query += f"{quote}{vid}{quote}:({','.join([quote+str(value)+quote if properties_types[self.properties[i]] == 'string' else str(value) for i, value in enumerate(properties)])}),"
                    else:
                        query += f"{quote}{vid}{quote}:({quote+str(properties)+quote if properties_types[self.properties[0]] == 'string' else str(properties)}),"
                # execute the last query
                query = query[:-1]
                result = session.execute(query)
                assert (
                    result.is_succeeded()
                ), f"Failed to write data: {result.error_msg()}"
            else:
                raise TypeError("Data should be a dict or a generator object")
        return True
