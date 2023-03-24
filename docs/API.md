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
    space="basketballplayer",
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