from code2flow import engine
from collections import deque, defaultdict
from collections import OrderedDict

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
    
def get_relevant_nodes_flow(node):
    subset_params = engine.SubsetParams(node.token, 2, 2)
    _, _, new_edges = engine._filter_for_subset(
        subset_params, all_nodes, edges, file_groups
    )
    return sort_nodes(new_edges)

def get_relevant_code(relevant_nodes):
    relevant_code = ""
    for node in relevant_nodes:
        for n in get_relevant_nodes_flow(node):
            if n.token != "(global)":
                relevant_code += n.code+"\n\n"


def sort_edges(edges):
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

def dedup_edges(edges):
    return list(OrderedDict.fromkeys(edges))

if __name__ == "__main__":
    base_file = "../src/codedoc/llm.py"
    map_file = "../src/codedoc/process.py"

    file_groups, all_nodes, edges = engine.map_it(
        [base_file, map_file], 
        "py", 
        False,
        [],
        [],
        [],
        [],
        False,
        engine.LanguageParams()
    )

    cross_edges = find_cross_edges(edges)

    relevant_nodes = get_relevant_nodes(cross_edges, base_file)

    get_relevant_code(relevant_nodes)