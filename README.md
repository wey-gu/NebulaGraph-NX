<img alt="NebulaGraph NetworkX Adaptor(ng_nx)" src="https://user-images.githubusercontent.com/1651790/227207918-7c023215-b7cf-4aa5-b734-bc50411dab77.png">

<p align="center">
    <em>Manipulate and analyze NebulaGraph data using the NetworkX API</em>
</p>

<p align="center">
<a href="LICENSE" target="_blank">
    <img src="https://img.shields.io/badge/License-Apache_2.0-blue.svg" alt="License">
</a>
<a href="https://badge.fury.io/py/ng_nx" target="_blank">
    <img src="https://badge.fury.io/py/ng_nx.svg" alt="PyPI version">
</a>
<a href="https://pdm.fming.dev" target="_blank">
    <img src="https://img.shields.io/badge/pdm-managed-blueviolet" alt="pdm-managed">
</a>
</p>

---

**Documentation**: <a href="https://github.com/wey-gu/nebulagraph-nx#documentation" target="_blank">https://github.com/wey-gu/nebulagraph-nx#documentation</a>

**Source Code**: <a href="https://github.com/wey-gu/nebulagraph-nx" target="_blank">https://github.com/wey-gu/nebulagraph-nx</a>

---

NebulaGraph NetworkX (ng_nx) is a powerful tool that bridges NebulaGraph and NetworkX, enabling you to leverage NetworkX's rich set of graph algorithms and analysis tools on data stored in NebulaGraph. This integration combines NebulaGraph's advanced storage capabilities with NetworkX's extensive graph analysis functionality.

## Quick Start

### Prerequisites

Ensure you have a NebulaGraph cluster running. For a quick setup, you can use [NebulaGraph Lite](https://github.com/nebula-contrib/nebulagraph-lite) to set up a cluster in Colab within 5 minutes.

### Installation

```bash
pip install ng_nx
```

### Run Algorithm on NebulaGraph

```python
from ng_nx import NebulaReader
from ng_nx.utils import NebulaGraphConfig

import networkx as nx

config = NebulaGraphConfig(
    space="basketballplayer",
    graphd_hosts="127.0.0.1:9669",
    metad_hosts="127.0.0.1:9559"
)

reader = NebulaReader(
    edges=["follow", "serve"],
    properties=[["degree"], ["start_year", "end_year"]],
    nebula_config=config, limit=10000)

g = reader.read()

pr = nx.pagerank(
    g, alpha=0.85,
    max_iter=100,
    tol=1e-06,
    weight='degree')

import community as community_louvain

ug = g.to_undirected()
louvain = community_louvain.best_partition(ug)
```

### Write Result to NebulaGraph

#### Create Schema for the result writing

```ngql
CREATE TAG IF NOT EXISTS pagerank (
    pagerank double NOT NULL
);

CREATE TAG IF NOT EXISTS louvain (
    cluster_id int NOT NULL
);
```

```python
from ng_nx import NebulaWriter

pr_writer = NebulaWriter(data=pr, nebula_config=config)

# properties to write
properties = ["pagerank"]

pr_writer.set_options(
    label="pagerank",
    properties=properties,
    batch_size=256,
    write_mode="insert",
    sink="nebulagraph_vertex",
)
# write back to NebulaGraph
pr_writer.write()

# write louvain result

louvain_writer = NebulaWriter(data=louvain, nebula_config=config)
# properties to write
properties = ["cluster_id"]
louvain_writer.set_options(
    label="louvain",
    properties=properties,
    batch_size=256,
    write_mode="insert",
    sink="nebulagraph_vertex",
)
louvain_writer.write()
```

### Using NebulaQueryReader

The `NebulaQueryReader` allows you to execute any NebulaGraph query and construct a NetworkX graph from the result.

```python
from ng_nx import NebulaQueryReader
from ng_nx.utils import NebulaGraphConfig

config = NebulaGraphConfig(
    space="demo_basketballplayer",
    graphd_hosts="127.0.0.1:9669",
    metad_hosts="127.0.0.1:9559"
)

reader = NebulaQueryReader(nebula_config=config)

# Execute a custom query
query = "MATCH p=(v:player{name:'Tim Duncan'})-[e:follow*1..3]->(v2) RETURN p"
g = reader.read(query)
```

This approach allows you to leverage the full power of NebulaGraph's query language while still being able to analyze the results using NetworkX.

## Readers

NG-NX provides three types of readers to fetch data from NebulaGraph:

1. `NebulaReader`: Reads a graph from NebulaGraph based on specified edges and properties, returning a NetworkX graph. It uses the MATCH clause internally to fetch data from NebulaGraph.

2. `NebulaQueryReader`: Executes a custom NebulaGraph query and constructs a NetworkX graph from the result. This reader is particularly useful when you need to perform complex queries or have specific data retrieval requirements.

3. `NebulaScanReader` (Coming soon): Will read graph data from NebulaGraph using a configuration similar to `NebulaReader`, but it will bypass the MATCH clause and utilize the SCAN interface with the Storage Client for potentially improved performance on large datasets.

Each reader is designed to cater to different use cases, providing flexibility in how you interact with and retrieve data from NebulaGraph for analysis with NetworkX.

## Documentation

[API Reference](https://github.com/wey-gu/nebulagraph-nx/blob/main/docs/API.md)