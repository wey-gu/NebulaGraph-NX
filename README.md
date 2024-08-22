<img alt="NebulaGraph NetworkX Adaptor(ng_nx)" src="https://github.com/user-attachments/assets/9a66411b-db9d-4243-a47f-1719221b335d">

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

## Table of Contents

- [Introduction](#introduction)
- [Features](#features)
- [Installation](#installation)
- [Usage](#usage)
  - [Reading Data from NebulaGraph](#reading-data-from-nebulagraph)
  - [Running Algorithms](#running-algorithms)
  - [Writing Results Back to NebulaGraph](#writing-results-back-to-nebulagraph)
- [Advanced Usage](#advanced-usage)
  - [NebulaQueryReader](#nebulaqueryreader)
- [Readers](#readers)
- [Documentation](#documentation)
- [Contributing](#contributing)

## Introduction

NebulaGraph NetworkX (ng_nx) is a powerful tool that bridges NebulaGraph and NetworkX, enabling you to leverage NetworkX's rich set of graph algorithms and analysis tools on data stored in NebulaGraph. This integration combines NebulaGraph's advanced storage capabilities with NetworkX's extensive graph analysis functionality.

## Features

- Seamless integration between NebulaGraph and NetworkX
- Multiple reader types for flexible data retrieval
- Easy-to-use writers for storing analysis results back to NebulaGraph
- Support for both vertex and edge data operations
- Compatibility with NetworkX's extensive library of graph algorithms

## Installation

Ensure you have a NebulaGraph cluster running. For a quick setup, you can use [NebulaGraph Lite](https://github.com/nebula-contrib/nebulagraph-lite) to set up a cluster in Colab within 5 minutes.

Install ng_nx using pip:

```bash
pip install ng_nx
```

## Usage

### Reading Data from NebulaGraph

> With GraphD Client

```python
from ng_nx import NebulaReader
from ng_nx.utils import NebulaGraphConfig

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
```

> With Storage Client, this requires ng_nx being run within NebulaGraph Network or expose the metad and storaged to it, with same host and port being registered in NebulaGraph(`SHOW HOSTS META;` and `SHOW HOSTS;`).

```python
from ng_nx import NebulaScanReader
from ng_nx.utils import NebulaGraphConfig

# Here, we need to be able to resolve the metad and storaged hosts, where they are the same with `SHOW HOSTS META;` and `SHOW HOSTS;`

config = NebulaGraphConfig(
    space="demo_basketballplayer",
    graphd_hosts="graphd0:9669",
    metad_hosts="metad0:9559"
)

reader = NebulaScanReader(
    edges=["follow", "serve"],
    properties=[["degree"], ["start_year", "end_year"]],
    nebula_config=config, limit=10000, with_rank=True)

g = reader.read()
```

### Running Algorithms

We need to install louvain and graspologic first, to run louvain and leiden algorithm that are not included in NetworkX(not like Pagerank etc).

```bash
pip3 install python-louvain graspologic
```

Then we can run the algorithms.

```python
import networkx as nx
import community as community_louvain

# Run PageRank algorithm
pr = nx.pagerank(
    g, alpha=0.85,
    max_iter=100,
    tol=1e-06,
    weight='degree')

# Run Louvain community detection
ug = g.to_undirected()
louvain = community_louvain.best_partition(ug)

# Run Leiden community detection

from graspologic.partition import hierarchical_leiden

# Cast Multi-Graph to Homogeneous Graph
g = nx.Graph(g)
community_hierarchical_clusters = hierarchical_leiden(ug, max_cluster_size=10)
```

### Writing Results Back to NebulaGraph

Typical use cases are:

1. Write the result of graph algorithm to NebulaGraph as vertex data.
2. Write the result of graph algorithm to NebulaGraph as edge data.

#### Write Vertex Data to NebulaGraph after Graph Analysis

We could create schema for pagerank and louvain like this:

```sql
CREATE TAG IF NOT EXISTS pagerank (
    pagerank double NOT NULL
);

CREATE TAG IF NOT EXISTS louvain (
    cluster_id int NOT NULL
);
```

Then we can run pagerank and louvain algorithm and write the result to NebulaGraph like this:

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
louvain_writer.write() # write back to NebulaGraph

```

#### Write Edge Data to NebulaGraph after Graph Analysis

Say we have a graph with player and follow edge, we can write the result to NebulaGraph like this:

```sql
CREATE TAG IF NOT EXISTS player (
    name string NOT NULL,
    age int NOT NULL
);

CREATE EDGE IF NOT EXISTS follow (
    start_year int NOT NULL,
    end_year int NOT NULL
);
```

We can write the result to NebulaGraph like this:

```python
from ng_nx import NebulaWriter

# Example edge data
edge_data = [
    ("player1", "player2", 0, [2022, 2023]),  # src, dst, rank, [start_year, end_year]
    ("player2", "player3", 1, [2021, 2022]),
    # ... more edges ...
]

edge_writer = NebulaWriter(data=edge_data, nebula_config=config)

# properties to write, map the properties to the edge data
properties = ["start_year", "end_year"]

edge_writer.set_options(
    label="follow",  # Edge type name
    properties=properties,
    batch_size=256,
    write_mode="insert",
    sink="nebulagraph_edge",
)

# Write edges to NebulaGraph
edge_writer.write()
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

## Advanced Usage

### NebulaQueryReader

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

## Readers

NG-NX provides three types of readers to fetch data from NebulaGraph:

1. `NebulaReader`(**Load from Edge and Properties via MATCH**): Reads a graph from NebulaGraph based on specified edges and properties, returning a NetworkX graph. It uses the MATCH clause internally to fetch data from NebulaGraph.

2. `NebulaQueryReader`(**Construct from Any Query**): Executes a custom NebulaGraph query and constructs a NetworkX graph from the result. This reader is particularly useful when you need to perform complex queries or have specific data retrieval requirements.

3. `NebulaScanReader`(**Better for LARGE datasets**): Will read graph data from NebulaGraph using a configuration similar to `NebulaReader`, but it will bypass the MATCH clause and utilize the SCAN interface with the Storage Client for potentially improved performance on large datasets. Note that this reader requires the NebulaGraph cluster to configure the metad and storaged accessible from the ng_nx.

Each reader is designed to cater to different use cases, providing flexibility in how you interact with and retrieve data from NebulaGraph for analysis with NetworkX.

## Documentation

[API Reference](https://github.com/wey-gu/nebulagraph-nx/blob/main/docs/API.md)

## Contributing

Contributions are welcome! If you find any issues or have suggestions for improvements, please open an issue or submit a pull request on the [GitHub repository](https://github.com/wey-gu/nebulagraph-nx).
