## NebulaReader

```python
from ng_nx import NebulaReader
from ng_nx.utils import NebulaGraphConfig

import networkx as nx

config_dict = {
    "graphd_hosts": "127.0.0.1:9669",
    "user": "root",
    "password": "nebula",
    "space": "basketballplayer",
}
config = NebulaGraphConfig(**config_dict)

reader = NebulaReader(
    edges=["follow", "serve"],
    properties=[["degree"], ["start_year", "end_year"]],
    with_rank=True, # this enable the multi-graph, and the edge_key is "__rank__" from NebulaGraph rank(edge)
    nebula_config=config, limit=100)

g = reader.read()

# call pagerank algorithm
pr = nx.pagerank(
    g, alpha=0.85,
    max_iter=100,
    tol=1e-06,
    weight='degree')
```


## NebulaQueryReader

The `NebulaQueryReader` allows you to execute any NebulaGraph query and construct a NetworkX graph from the result.

```python
from ng_nx import NebulaQueryReader
from ng_nx.utils import NebulaGraphConfig

config = NebulaGraphConfig(
    space="demo_basketballplayer",
    graphd_hosts="127.0.0.1:9669",
    metad_hosts="127.0.0.1:9559"
)

reader = NebulaQueryReader(
    query="MATCH p=(v:player{name:'Tim Duncan'})-[e:follow*1..3]->(v2) RETURN p",
    nebula_config=config,
    limit=10000,
    with_rank=True,
)

g = reader.read()
```

## NebulaScanReader

The `NebulaScanReader` allows you to scan all vertexes and edges in NebulaGraph, and construct a NetworkX graph from the result.

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

## NebulaWriter

Let's write them back to tag: pagerank(pagerank) and louvain(cluster_id). So we create TAGs in NebulaGraph on same space with the following schema:

```ngql
CREATE TAG IF NOT EXISTS pagerank (
    pagerank double NOT NULL
);
CREATE TAG IF NOT EXISTS louvain (
    cluster_id int NOT NULL
);
```

And we could write the result back to NebulaGraph with the following code:

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

Then we could verify the result:

```cypher
(root@nebula) [basketballplayer]>

MATCH (n)
    RETURN properties(n).name, n.pagerank.pagerank, n.louvain.cluster_id
    LIMIT 5
+--------------------+-----------------------+----------------------+
| properties(n).name | n.pagerank.pagerank   | n.louvain.cluster_id |
+--------------------+-----------------------+----------------------+
| "Tracy McGrady"    | 0.015888952964973516  | 4                    |
| "Luka Doncic"      | 0.008918675093514758  | 1                    |
| "Spurs"            | 0.008266820546396887  | 6                    |
| "Raptors"          | 0.005000457949346969  | 4                    |
| "Heat"             | 0.0038279814310668457 | 2                    |
+--------------------+-----------------------+----------------------+
Got 5 rows (time spent 47723/58029 us)

Mon, 27 Mar 2023 13:45:40 CST
```