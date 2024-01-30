import ast
from collections import OrderedDict, defaultdict, deque

from code2flow import engine

class DepsParser:
    def extract_dependency_code(self, base_file, *files):
        """extracts the code that is relevant to the base file"""
        files = [base_file] + list(files)
        groups, nodes, edges = self.parse_files(files)
        self.trim_dependencies(groups, nodes, edges, base_file)
        code = ""
        for file_ in groups:
            code += f"\n\n\n### FILE {file_.path}\n\n"
            code += ast.unparse(file_.node)
        return code

    def parse_files(self, files: list):
        """parses groups, nodes and edges from the files"""
        return engine.map_it(files)

    def trim_dependencies(self, groups, nodes, edges, base_file):
        """removes all nodes and edges that are not related to the base file"""
        dependency_nodes = self._get_dependency_nodes(groups, nodes, edges, base_file)
        for file_ in groups:
            for child in file_.node.body[:]:
                if child not in dependency_nodes:
                    file_.node.body.remove(child)
                elif isinstance(child, ast.ClassDef):
                    for grandchild in child.body[:]:
                        if (
                            type(grandchild) in (ast.FunctionDef, ast.AsyncFunctionDef)
                            and grandchild not in dependency_nodes
                        ):
                            child.body.remove(grandchild)
    
    def _get_dependency_nodes(self, groups, nodes, edges, base_file):
        """returns the nodes that are found in the base file and spread across multiple files"""
        cross_edges = self._find_cross_edges(edges)
        dependency_nodes = []
        for base_node in self._get_base_nodes(cross_edges, base_file):
            for node in self._get_nodes_execution_flow(base_node, groups, nodes, edges):
                dependency_nodes.append(node.node)
                if node.parent.group_type == "CLASS":
                    dependency_nodes.append(node.parent.node)
        return dependency_nodes
    
    def _find_cross_edges(self, edges):
        """finds edges that cross file boundaries"""
        self._add_parents_attr(edges)
        cross_edges = []
        for edge in edges:
            if edge.node0.file_token != edge.node1.file_token:
                cross_edges.append(edge)
        return cross_edges

    def _add_parents_attr(self, edges):
        """adds some addidional attributes from the parent nodes"""
        for edge in edges:
            self._add_nodes_attrs(edge.node0, edge.node0)
            self._add_nodes_attrs(edge.node1, edge.node1)

    def _add_nodes_attrs(self, orig_node, node):
        """recursively adds attributes from parent nodes"""
        if node.parent.group_type == "FILE":
            orig_node.file_token = node.parent.token
            orig_node.path = node.parent.path
        else:
            self._add_nodes_attrs(orig_node, node.parent)

    def _get_base_nodes(self, cross_edges, base_file):
        """return the nodes which are found in the base file"""
        relevant_nodes = []
        for cross_edge in cross_edges:
            if cross_edge.node0.path == base_file:
                relevant_nodes.append(cross_edge.node0)
            else:
                relevant_nodes.append(cross_edge.node1)
        return relevant_nodes
    
    def _get_nodes_execution_flow(self, node, groups, nodes, edges):
        """get the execution flow of nodes related to executing a specific node"""
        subset_params = engine.SubsetParams(node.token, 2, 2)
        _, _, new_edges = engine._filter_for_subset(subset_params, nodes, edges, groups)
        return self._sort_nodes(new_edges)

    def _sort_nodes(self, edges):
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

    def build_execution_graph(self, base_file, *files):
        graph = self._build_graph(base_file, *files)
        # Find the root nodes
        root_node = set(graph.keys()) - {
            neighbor for neighbors in graph.values() for neighbor in neighbors
        }
        # Convert the graph to a string starting from the root nodes
        graph_string = ""
        for node in root_node:
            graph_string += self._graph_to_string(node, graph)

        return graph_string

    def _build_graph(self, base_file, *files):
        """builds a graph of the execution flow of the base file"""
        graph = defaultdict(list)
        files = [base_file] + list(files)
        groups, nodes, edges = self.parse_files(files)
        cross_edges = self._find_cross_edges(edges)
        for node in self._get_base_nodes(cross_edges, base_file):
            for edge in self._get_edges_execution_flow(node, groups, nodes, edges):
                name0, name1 = self._add_class_names(edge.node0, edge.node1)
                graph[name0].append(name1)
        return graph
    
    def _add_class_names(self, node0, node1):
        """adds the class names to the nodes"""
        if node0.parent.group_type == "CLASS":
            name0 = f"{node0.parent.token}.{node0.token}"
        else:
            name0 = node0.token
        if node1.parent.group_type == "CLASS":
            name1 = f"{node1.parent.token}.{node1.token}"
        else:
            name1 = node1.token
        return name0, name1

    def _get_edges_execution_flow(self, node, groups, nodes, edges):
        """get the execution flow of edges related to executing a specific node"""
        subset_params = engine.SubsetParams(node.token, 2, 2)
        _, _, new_edges = engine._filter_for_subset(subset_params, nodes, edges, groups)
        sorted_edges = self._sort_edges(new_edges)
        dedup_edges = list(OrderedDict.fromkeys(sorted_edges))
        return dedup_edges

    def _sort_edges(self, edges):
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

    def _graph_to_string(self, node, graph, depth=0):
        """converts a graph to string format"""
        
        arrow = "-> Calls " if depth != 0 else ""
        result = f"    " * depth + arrow + node + "()\n"
        for neighbor in graph[node]:
            result += self._graph_to_string(neighbor, graph, depth + 1)
        return result


if __name__ == "__main__":
    pars = DepsParser()
    graph = pars.extract_dependency_code("./src/codedoc/process.py", "./src/codedoc/executor.py")
    print(graph)
    # print(extract_dependency_code("./src/codedoc/process.py", "./src/codedoc/llm.py"))
    # print(build_dependency_graph("./src/codedoc/process.py", "./src/codedoc/llm.py"))
