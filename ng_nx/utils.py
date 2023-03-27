# SPDX-License-Identifier: Apache-2.0
# Copyright 2023 The NebulaGraph Authors. All rights reserved.

from __future__ import annotations

from typing import Dict

import pandas as pd
from nebula3.data.DataObject import Value, ValueWrapper
from nebula3.data.ResultSet import ResultSet

# Default Configuration
GRAPHD_HOSTS = "graphd:9669"
METAD_HOSTS = "metad0:9559,metad1:9559,metad2:9559"
USER = "root"
PASSWORD = "nebula"
SPACE = "basketballplayer"

# TBD when https://github.com/vesoft-inc/nebula-python/pull/269 is merged
# in a release version of nebula-python, I could leverage the ValueWrapper.cast()
# method to simplify the code below
cast_as = {
    Value.NVAL: "as_null",
    Value.BVAL: "as_bool",
    Value.IVAL: "as_int",
    Value.FVAL: "as_double",
    Value.SVAL: "as_string",
    Value.LVAL: "as_list",
    Value.UVAL: "as_set",
    Value.MVAL: "as_map",
    Value.TVAL: "as_time",
    Value.DVAL: "as_date",
    Value.DTVAL: "as_datetime",
    Value.VVAL: "as_node",
    Value.EVAL: "as_relationship",
    Value.PVAL: "as_path",
    Value.GGVAL: "as_geography",
    Value.DUVAL: "as_duration",
}


def cast(val: ValueWrapper):
    _type = val._value.getType()
    if _type == Value.__EMPTY__:
        return None
    if _type in cast_as:
        return getattr(val, cast_as[_type])()
    if _type == Value.LVAL:
        return [x.cast() for x in val.as_list()]
    if _type == Value.UVAL:
        return {x.cast() for x in val.as_set()}
    if _type == Value.MVAL:
        return {k: v.cast() for k, v in val.as_map().items()}


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
        d[col_name] = [cast(x) for x in col_list]
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
