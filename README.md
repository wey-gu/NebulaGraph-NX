<img alt="NebulaGraph NetworkX Adaptor(ng_nx)" src="https://user-images.githubusercontent.com/1651790/227207918-7c023215-b7cf-4aa5-b734-bc50411dab77.png">

<p align="center">
    <em>Manipulation of graphs in NebulaGraph using the NetworkX API.</em>
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

<!-- <a href="https://github.com/wey-gu/nebulagraph-nx/actions/workflows/ci.yml">
  <img src="https://github.com/wey-gu/nebulagraph-nx/actions/workflows/ci.yml/badge.svg" alt="Tests">
</a> -->

</p>

---

**Documentation**: <a href="https://github.com/wey-gu/nebulagraph-nx#documentation" target="_blank">https://github.com/wey-gu/nebulagraph-nx#documentation</a>

**Source Code**: <a href="https://github.com/wey-gu/nebulagraph-nx" target="_blank">https://github.com/wey-gu/nebulagraph-nx</a>

---

NebulaGraph NetworkX (ng_nx) is a tool that allows you to use the NetworkX API for manipulating graphs in NebulaGraph. It makes it easy to analyze and manipulate graphs using NebulaGraph's advanced capabilities while still using the familiar NetworkX interface. In short, ng_nx bridges the gap between NebulaGraph and NetworkX.

## Quick Start

### Install

```bash
pip install ng_nx
```

### Run Pagerank on NebulaGraph

```python
from ng_nx import NebulaReader
from ng_nx.utils import NebulaGraphConfig

import networkx as nx

config = NebulaGraphConfig()

reader = NebulaReader(
    space="basketballplayer",
    edges=["follow", "serve"],
    properties=[["degree"], ["start_year", "end_year"]],
    nebula_config=config, limit=10000)

g = reader.read()

pr = nx.pagerank(
    g, alpha=0.85,
    max_iter=100,
    tol=1e-06,
    weight='degree')
```

## Documentation

[API Reference](https://github.com/wey-gu/nebulagraph-nx/blob/main/docs/API.md)