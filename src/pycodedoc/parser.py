import ast
import copy
import os
from fnmatch import fnmatch
from pathlib import Path
from typing import Any, List, Union

from code2flow import engine
from pydantic import BaseModel, Field, PrivateAttr

from pycodedoc.utils import set_logger

CONFIG = {
    "include_file_patterns": ["*.py"],
    "exclude_patterns": [".*", "__*"],
}

logger = set_logger()


class Function(BaseModel):
    name: str
    uname: str
    path: str
    node: object
    code: str
    type: str = "function"
    is_method: bool


class Class(BaseModel):
    name: str
    path: str
    node: object
    code: str
    type: str = "class"
    methods: List[Function] = Field(default_factory=list)

    def parse_methods(self):
        for node in self.node.body:
            if type(node) in (ast.AsyncFunctionDef, ast.FunctionDef):
                self.methods.append(
                    Function(
                        name=node.name,
                        uname=f"{self.name}.{node.name}",
                        path=self.path,
                        node=node,
                        code=ast.unparse(node),
                        is_method=True,
                    )
                )


class Module(BaseModel):
    path: str
    node: object
    code: str
    entities: List[Union[Function, Class]] = Field(default_factory=list)
    name: str = ""

    def model_post_init(self, __context: Any) -> None:
        self.name = os.path.splitext(os.path.split(self.path)[-1])[0]

    def parse_entities(self):
        for node in self.node.body:
            if isinstance(node, ast.ClassDef):
                class_ = Class(
                    name=node.name, path=self.path, node=node, code=ast.unparse(node)
                )
                class_.parse_methods()
                self.entities.append(class_)
            elif type(node) in (ast.AsyncFunctionDef, ast.FunctionDef):
                self.entities.append(
                    Function(
                        name=node.name,
                        uname=node.name,
                        path=self.path,
                        node=node,
                        code=ast.unparse(node),
                        is_method=False,
                    )
                )


class Parser(BaseModel):
    base_dir: str = "."
    exclude_patterns: list = CONFIG["exclude_patterns"]
    include_file_patterns: list = CONFIG["include_file_patterns"]
    strip_imports: bool = False
    strip_globals: bool = True
    _modules: List[Module] = PrivateAttr(default_factory=list)

    def model_post_init(self, __context: Any) -> None:
        self.parse_modules()

    def parse_modules(self):
        for module_path in self.get_modules_paths():
            self._modules.append(self.parse_module(module_path))

    def parse_module(self, module_path: str) -> Module:
        with open(os.path.join(self.base_dir, module_path), "r") as source:
            module = source.read()
        node = ast.parse(module)
        module = Module(path=module_path, node=node, code=ast.unparse(node))
        module.parse_entities()
        return module

    def get_modules(self, module_path: str = None, attr: str = None):
        if module_path:
            absolute_module_path = os.path.abspath(
                os.path.join(self.base_dir, module_path)
            )
            modules = [
                module
                for module in self._modules
                if os.path.abspath(os.path.join(self.base_dir, module.path))
                == absolute_module_path
            ]
        else:
            modules = self._modules
        if attr:
            return [getattr(module, attr) for module in modules]
        else:
            return modules

    def get_module(self, module_path: str, attr: str = None):
        if attr is None:
            return self.get_modules(module_path)[0]
        else:
            return getattr(self.get_modules(module_path)[0], attr)

    def get_classes(self, module_path: str = None, attr: str = None):
        modules = self.get_modules(module_path)
        classes = []
        for module in modules:
            for entity in module.entities:
                if isinstance(entity, Class):
                    classes.append(entity)

        if attr:
            return [getattr(class_, attr) for class_ in classes]
        else:
            return classes

    def get_functions(self, module_path: str = None, attr: str = None):
        modules = self.get_modules(module_path)
        functions = []
        for module in modules:
            for entity in module.entities:
                if isinstance(entity, Function):
                    functions.append(entity)
                elif isinstance(entity, Class):
                    functions.extend(entity.methods)

        if attr:
            return [getattr(function, attr) for function in functions]
        else:
            return functions

    def get_entities(self, module_path: str = None, attr: str = None):
        modules = self.get_modules(module_path)
        entities = []
        for module in modules:
            entities.extend(module.entities)

        if attr:
            return [getattr(entity, attr) for entity in entities]
        else:
            return entities

    def get_code_structure(
        self,
        entity: Union[Function, Module, Class],
        descriptions: dict = None,
        copy_entity: bool = False,
    ):
        if copy_entity:
            entity = copy.deepcopy(entity)
        if isinstance(entity, Module):
            self.parse_module_structure(entity.node, descriptions)
        elif isinstance(entity, Class):
            self.parse_class_structure(entity.node, descriptions)
        elif isinstance(entity, Function):
            self.parse_function_structure(entity.node, descriptions)
        return ast.unparse(entity.node)

    def get_deps_code(
        self,
        module: Module,
        deps: List[Module],
        output_dir: str,
        create_graphs: bool = False,
    ):
        module = copy.deepcopy(module)
        deps = [copy.deepcopy(dep) for dep in deps]
        groups, nodes, edges, execution_graph = self.parse_module_deps(module, deps)
        if create_graphs:
            file_path = os.path.join(output_dir, "graphs", f"{module.name}_deps.gv")
            self._write_graphs(groups, nodes, edges, file_path)
        deps_code = self.concat_dep_code(deps)
        return ast.unparse(module.node), deps_code, execution_graph

    def concat_dep_code(self, deps):
        deps_code = ""
        for dep in deps:
            deps_code += f"\n\nFILE {dep.name}.py:\n\n"
            deps_code += ast.unparse(dep.node)
        return deps_code

    def write_graphs(self, module: Module, output_dir: str):
        groups, nodes, edges = self.parse_files_flows(
            [os.path.join(self.base_dir, module.path)]
        )
        file_path = os.path.join(output_dir, "graphs", f"{module.name}.gv")
        self._write_graphs(groups, nodes, edges, file_path)

    def _write_graphs(self, groups, nodes, edges, file_path):
        if any(edges):
            if not os.path.exists(os.path.dirname(file_path)):
                os.makedirs(os.path.dirname(file_path))
            try:
                with open(file_path, "w") as fh:
                    engine.write_file(
                        fh,
                        nodes=nodes,
                        edges=edges,
                        groups=groups,
                        hide_legend=False,
                        no_grouping=False,
                        as_json=False,
                    )
                png_file_path = os.path.splitext(file_path)[0] + ".png"
                engine._generate_final_img(file_path, "png", png_file_path, len(edges))
            except FileNotFoundError as e:
                if e.filename == "dot":
                    logger.error(
                        "Graphviz is not installed correctly. Please install it to generate the graphs."
                    )
                    os.remove(file_path)
                    os.remove(png_file_path)
                else:
                    raise e
            except Exception as e:
                raise e
        # else:
        #     logging.warning(f"No graph is created for {file_path} as no execution flow is found.")

    def parse_function_structure(
        self,
        node: Union[ast.FunctionDef, ast.AsyncFunctionDef],
        descriptions: dict = None,
    ):
        node.body = []
        if descriptions:
            # add docstring to function body
            docstring = descriptions[node.name]
            node.body.append(ast.Expr(ast.Constant(docstring)))
        # add ellipsis to function body
        node.body.append(ast.Expr(ast.Constant(...)))

    def parse_class_structure(self, node: ast.ClassDef, descriptions: dict = None):
        for child in node.body:
            if type(child) in (ast.FunctionDef, ast.AsyncFunctionDef):
                child.body = []
                if descriptions:
                    # add docstring to child body
                    docstring = descriptions[f"{node.name}.{child.name}"]
                    child.body.append(ast.Expr(ast.Constant(docstring)))
                # add ellipsis to child body
                child.body.append(ast.Expr(ast.Constant(...)))

    def parse_module_structure(self, node: ast.Module, descriptions: dict = None):
        for child in node.body[:]:
            if type(child) in (ast.FunctionDef, ast.AsyncFunctionDef):
                self.parse_function_structure(child, descriptions)
            elif type(child) == ast.ClassDef:
                self.parse_class_structure(child, descriptions)
            elif type(child) in (ast.Import, ast.ImportFrom):
                if self.strip_imports:
                    node.body.pop(node.body.index(child))
            else:
                if self.strip_globals:
                    node.body.pop(node.body.index(child))

    def get_modules_paths(self):
        paths = []
        for path in self._get_paths_recursively(self.base_dir):
            paths.append(os.path.relpath(path, self.base_dir))
        return paths

    def _get_paths_recursively(self, path: str):
        paths = self._get_matching_paths(path)
        for path in paths:
            if path.is_dir():
                yield from self._get_paths_recursively(path)
            else:
                yield str(path)

    def _get_matching_paths(self, path):
        return list(
            path
            for path in Path(path).iterdir()
            if self._not_match(path, self.exclude_patterns)
            and self._match(path, self.include_file_patterns)
        )

    def _not_match(self, path: Path, patterns: list):
        if any(patterns):
            for pattern in patterns:
                if fnmatch(path.name, pattern):
                    return False
            return True
        else:
            return True

    def _match(self, path: Path, file_patterns: list, match_dir: bool = False):
        if any(file_patterns):
            if path.is_file():
                return any([fnmatch(path.name, pattern) for pattern in file_patterns])
            if match_dir and path.is_dir():
                return any(
                    [any(list(path.glob(f"**/{pattern}"))) for pattern in file_patterns]
                )
        return True

    def get_tree(self):
        tree = ""
        for path_element in self._get_tree_recursively(self.base_dir):
            tree += f"{path_element}\n"
        return tree

    def _get_tree_recursively(self, path: str, prefix: str = ""):
        paths = self._get_matching_paths(path)
        space = "    "
        branch = "│   "
        tee = "├── "
        last = "└── "
        # paths each get pointers that are ├── with a final └── :
        pointers = [tee] * (len(paths) - 1) + [last]
        for pointer, path in zip(pointers, paths):
            if path.is_dir() and self._match(path, self.include_file_patterns, True):
                yield prefix + pointer + path.name + "/"
            elif path.is_file():
                yield prefix + pointer + path.name

            if path.is_dir():  # extend the prefix and recurse:
                extension = branch if pointer == tee else space
                # i.e. space because last, └── , above so no more |
                yield from self._get_tree_recursively(path, prefix=prefix + extension)

    def get_module_deps(self, module_path: str):
        import_names = self.get_import_names(module_path)
        module_paths = self.get_modules_paths()
        module_names = self.get_module_names(module_paths)
        module_deps = []
        for module_name, module_path in zip(module_names, module_paths):
            if module_name in import_names:
                module_deps.extend(self.get_modules(module_path))
        return module_deps

    def get_import_names(self, module_path: str):
        module = self.get_module(module_path)
        module_names = []
        for node in module.node.body:
            if isinstance(node, ast.Import):
                for alias in node.names:
                    module_names.append(alias.name)
            elif isinstance(node, ast.ImportFrom):
                module_names.append(
                    node.module.split(".")[-1]
                )  # Get the last part of the module path
                for alias in node.names:
                    module_names.append(alias.name)
        return module_names

    def get_module_names(self, module_paths):
        return [os.path.splitext(os.path.split(path)[-1])[0] for path in module_paths]

    def parse_module_deps(self, module: Module, deps: List[Module]):
        module_paths = [os.path.join(self.base_dir, module.path)] + [
            os.path.join(self.base_dir, dep.path) for dep in deps
        ]
        # groups, nodes, edges = self._deps_parser.get_cross_entities(module_paths)
        groups, nodes, edges = self.parse_files_flows(module_paths)
        groups, nodes, edges = self.get_related_entities(groups, edges)
        nodes_in_common = [edge_node.token for edge_node in nodes]
        classes_in_common = [
            subgroup.token for group in groups for subgroup in group.subgroups
        ]

        for module in module, *deps:
            for child in module.node.body[:]:
                if type(child) in (ast.FunctionDef, ast.AsyncFunctionDef):
                    if child.name not in nodes_in_common:
                        module.node.body.remove(child)
                elif type(child) == ast.ClassDef:
                    if child.name not in classes_in_common:
                        module.node.body.remove(child)
                    else:
                        for subchild in child.body[:]:
                            if type(subchild) in (
                                ast.FunctionDef,
                                ast.AsyncFunctionDef,
                            ):
                                if subchild.name not in nodes_in_common:
                                    child.body.remove(subchild)

                elif type(child) in (ast.Import, ast.ImportFrom):
                    if self.strip_imports:
                        module.node.body.remove(child)
                else:
                    if self.strip_globals:
                        module.node.body.remove(child)
        execution_flow = ""
        for edge in edges:
            execution_flow += f"{edge.node0.file_token}.py {edge.node0.token}() -> {edge.node1.file_token}.py {edge.node1.token}()\n"
        return groups, nodes, edges, execution_flow

    def parse_files_flows(self, paths: list):
        # paths = [os.path.join(self.base_dir, file_) for file_ in files]
        return engine.map_it(
            paths,
            extension="py",
            no_trimming=False,
            exclude_namespaces=[],
            exclude_functions=[],
            include_only_namespaces=[],
            include_only_functions=[],
            skip_parse_errors=False,
            lang_params=engine.LanguageParams(),
        )

    def get_related_entities(self, groups, edges):
        cross_edges = self._find_cross_edges(edges)
        cross_nodes = self._get_edge_nodes(cross_edges)
        cross_groups = engine._filter_groups_for_subset(cross_nodes, groups)
        return cross_groups, cross_nodes, cross_edges

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
            # orig_node.path = node.parent.path
        else:
            self._add_nodes_attrs(orig_node, node.parent)

    def _get_edge_nodes(self, edges):
        edge_nodes = set()
        for edge in edges:
            edge_nodes.add(edge.node0)
            edge_nodes.add(edge.node1)
        return list(edge_nodes)


# if __name__ == "__main__":

#     parser = Parser(base_dir="./src/pycodedoc")
#     a,b,c = parser.parse_files_flows(["parser.py", "docgen.py"])
#     a,b,c = parser.get_related_entities(a,c)
#     print(a)
# parser.write_graphs(module)
# deps = parser.get_module_deps(module)
# a,b,c = parser.get_code_deps_structure(module, deps, True)
# print(a)
# print(b)
# print(c)
