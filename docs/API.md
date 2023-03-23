## NebulaReader

```python
from ng_nx import NebulaReader, NebulaGraphConfig
from networkx import nx

config_dict = {
    "graphd_hosts": "graphd:9669",
    "user": "root",
    "password": "nebula",
    "space": "basketballplayer",
}
config = NebulaGraphConfig(**config_dict)

reader = NebulaReader(
    space="basketballplayer",
    edges=["follow"],
    properties=[["degree"]],
    nebula_config=config, limit=100)

g = reader.read()

# call pagerank algorithm
pr = nx.pagerank(
    g, alpha=0.85,
    max_iter=100,
    tol=1e-06,
    weight='weight')
```
