from codedoc.deps import DepsParser
from code2flow import engine

parser = DepsParser(downstream_depth=2, upstream_depth=2)

groups, nodes, edges = parser.parse_files(["./src/codedoc/process.py", "./src/codedoc/parser.py", "./src/codedoc/llm.py"])

cross_edges = parser._find_cross_edges(edges)

edge_nodes = set()
for cross_edge in cross_edges:
    edge_nodes.add(cross_edge.node0)
    edge_nodes.add(cross_edge.node1)
    
with open("./test.gv", 'w') as fh:
    engine.write_file(fh, nodes=edge_nodes, edges=cross_edges,
                        groups=groups, hide_legend=False,
                        no_grouping=True, as_json=False)

engine._generate_final_img("./test.gv", "png", "./test.png", len(edges))