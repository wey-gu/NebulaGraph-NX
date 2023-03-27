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
    nebula_config=config, limit=100)

g = reader.read()

# call pagerank algorithm
pr = nx.pagerank(
    g, alpha=0.85,
    max_iter=100,
    tol=1e-06,
    weight='degree')
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