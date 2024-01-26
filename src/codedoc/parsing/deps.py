import ast
from code2flow import engine
from collections import deque, defaultdict
from collections import OrderedDict

def get_data(base_file, map_file):
    return engine.map_it([base_file, map_file])
    
def add_file_token(edges):
    for edge in edges:
        _add_file_token(edge.node0, edge.node0)
        _add_file_token(edge.node1, edge.node1)
    
def _add_file_token(orig_node, node):
    if node.parent.group_type == "FILE":
        orig_node.file_token = node.parent.token
        orig_node.path = node.parent.path
    else:
        _add_file_token(orig_node, node.parent)

def find_cross_edges(edges):
    add_file_token(edges)
    cross_edges = []
    for edge in edges:
        if edge.node0.file_token != edge.node1.file_token:
            cross_edges.append(edge)
    return cross_edges

def get_relevant_nodes(cross_edges, base_file):
    relevant_nodes = []
    for cross_edge in cross_edges:
        if cross_edge.node0.path == base_file:
            relevant_nodes.append(cross_edge.node0)
        else:
            relevant_nodes.append(cross_edge.node1)
    return relevant_nodes


def sort_nodes(edges):
    """topological sort so that nodes are in order of execution"""
    graph = defaultdict(list)
    in_degree = defaultdict(int)

    for edge in edges:
        graph[edge.node0].append(edge.node1)
        in_degree[edge.node1] += 1

    Q = deque(node for node in graph if in_degree[node] == 0)
    L = []

    while Q:
        node = Q.pop()
        L.append(node)
        for neighbor in graph[node]:
            in_degree[neighbor] -= 1
            if in_degree[neighbor] == 0:
                Q.appendleft(neighbor)

    if len(L) == len(graph):
        return L
    else:
        return []

def get_relevant_nodes_flow(node, groups, nodes, edges):
    subset_params = engine.SubsetParams(node.token, 2, 2)
    _, _, new_edges = engine._filter_for_subset(
        subset_params, nodes, edges, groups
    )
    return sort_nodes(new_edges)

def get_relevant_entity_nodes(groups, nodes, edges, base_file):
    cross_edges = find_cross_edges(edges)
    entity_nodes = []
    for relevant_node in get_relevant_nodes(cross_edges, base_file):
        for node in get_relevant_nodes_flow(relevant_node, groups, nodes, edges):
            entity_nodes.append(node.node)
            if node.parent.group_type == "CLASS":
                entity_nodes.append(node.parent.node)
    return entity_nodes

def trim_groups_dependencies(groups, nodes, edges, base_file):
    entity_nodes = get_relevant_entity_nodes(groups, nodes, edges, base_file)
    for file_ in groups:
        for child in file_.node.body[:]:
            if child not in entity_nodes:
                file_.node.body.remove(child)
            elif isinstance(child, ast.ClassDef):
                for grandchild in child.body[:]:
                    if (
                        type(grandchild) in (ast.FunctionDef, ast.AsyncFunctionDef) 
                        and grandchild not in entity_nodes
                    ):
                        child.body.remove(grandchild)

def extract_dependency_code(base_file, map_file):
    groups, nodes, edges = get_data(base_file, map_file)
    trim_groups_dependencies(groups, nodes, edges, base_file)
    code = ""
    for file_ in groups:
        code += f"\n\n\n### FILE {file_.path}\n\n"
        code += ast.unparse(file_.node)
    return code

from collections import defaultdict


def sort_edges(edges):
    """topological sort so that edges are in order of execution"""
    graph = defaultdict(list)
    in_degree = defaultdict(int)
    edge_dict = {}

    for edge in edges:
        graph[edge.node0].append(edge.node1)
        in_degree[edge.node1] += 1
        edge_dict[(edge.node0, edge.node1)] = edge

    Q = deque(node for node in graph if in_degree[node] == 0)
    L = []

    while Q:
        node = Q.pop()
        for neighbor in graph[node]:
            L.append(edge_dict[(node, neighbor)])
            in_degree[neighbor] -= 1
            if in_degree[neighbor] == 0:
                Q.appendleft(neighbor)

    if len(L) == len(edges):
        return L
    else:
        return []

def get_relevant_edges_flow(node, groups, nodes, edges):
    subset_params = engine.SubsetParams(node.token, 2, 2)
    _, _, new_edges = engine._filter_for_subset(
        subset_params, nodes, edges, groups
    )
    sorted_edges = sort_edges(new_edges)
    dedup_edges = list(OrderedDict.fromkeys(sorted_edges))
    return dedup_edges

def build_graph(base_file, map_file):
    graph = defaultdict(list)
    groups, nodes, edges = get_data(base_file, map_file)

    cross_edges = find_cross_edges(edges)
    for node in get_relevant_nodes(cross_edges, base_file):
        for edge in get_relevant_edges_flow(node, groups, nodes, edges):
            graph[edge.node0.token].append(edge.node1.token)
    
    return graph

def graph_to_string(node, graph, depth=0):
    result = '    ' * depth + node + '()\n'
    for neighbor in graph[node]:
        result += graph_to_string(neighbor, graph, depth + 1)
    return result

def build_dependency_graph(base_file, map_file):
    graph = build_graph(base_file, map_file)
    # Find the root node (assuming there's only one)
    root_node = set(graph.keys()) - {neighbor for neighbors in graph.values() for neighbor in neighbors}

    # Convert the graph to a string starting from the root node
    graph_string = ""
    for node in root_node:
        graph_string += graph_to_string(node, graph)

    return graph_string

if __name__ == "__main__":
    print(extract_dependency_code("./src/codedoc/process.py", "./src/codedoc/llm.py"))
    print(build_dependency_graph("./src/codedoc/process.py", "./src/codedoc/llm.py"))



