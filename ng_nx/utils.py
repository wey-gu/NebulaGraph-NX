# SPDX-License-Identifier: Apache-2.0
# Copyright 2023 The NebulaGraph Authors. All rights reserved.

from __future__ import annotations

from typing import Dict

import pandas as pd
from nebula3.data.ResultSet import ResultSet

# Default Configuration
GRAPHD_HOSTS = "graphd:9669"
METAD_HOSTS = "metad0:9559,metad1:9559,metad2:9559"
USER = "root"
PASSWORD = "nebula"
SPACE = "basketballplayer"


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


class NebulaGraphConfig:
    def __init__(
        self,
        graphd_hosts: str = GRAPHD_HOSTS,
        metad_hosts: str = METAD_HOSTS,
        user: str = USER,
        password: str = PASSWORD,
        space: str = SPACE,
        **kwargs,
    ):
        self.graphd_hosts = graphd_hosts
        self.metad_hosts = metad_hosts
        self.user = user
        self.password = password
        self.space = space
        self.shuffle_partitions = None
        self.executor_memory = None
        self.driver_memory = None
        for key, value in kwargs.items():
            setattr(self, key, value)

    def __getattr__(self, name):
        return None
