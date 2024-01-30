import ast
from typing import Any, List, Union
from pydantic import BaseModel, PrivateAttr, Field
from fnmatch import fnmatch
from pathlib import Path

CONFIG = {
    "include_file_patterns": ["*.py"],
    "exclude_patterns": [".*", "__*"],
}


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
    entities: List[Union[Function, Class]] = Field(default_factory=list)

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
    _modules: List[Module] = PrivateAttr(default_factory=list)

    def model_post_init(self, __context: Any) -> None:
        self.parse_modules()

    def parse_modules(self):
        for module_path in self.get_modules_paths():
            self._modules.append(self.parse_module(module_path))

    def parse_module(self, module_path: str) -> Module:
        with open(module_path, "r") as source:
            module = source.read()
        node = ast.parse(module)
        module = Module(path=module_path, node=node)
        module.parse_entities()
        return module

    def get_modules(self, module_path: str = None, attr: str = None):
        if module_path:
            modules = [module for module in self._modules if module.path == module_path]
        else:
            modules = self._modules
        if attr:
            return [getattr(module, attr) for module in modules]
        else:
            return modules

    def get_functions(self, module_path: str = None, attr: str = None):
        if module_path:
            modules = [module for module in self._modules if module.path == module_path]
        else:
            modules = self._modules

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
        if module_path:
            modules = [module for module in self._modules if module.path == module_path]
        else:
            modules = self._modules

        entities = []
        for module in modules:
            entities.extend(module.entities)

        if attr:
            return [getattr(entity, attr) for entity in entities]
        else:
            return entities
    
    def get_modules_structure(self, module_path: str = None, desc: dict = None):
        structures = []
        for module in self.get_modules(module_path):
            structure = f"\n\n### FILE {module.path}\n"
            for entity in module.entities:
                if entity.type == "class":
                    structure += f"\nclass {entity.name}()\n"
                    for method in entity.methods:
                        if desc:
                            definition = desc[method.path][method.uname]
                            structure += f"    def {method.name}() -> {definition}\n"
                        else:
                            structure += f"    def {method.name}()\n"
                elif entity.type == "function":
                    if desc:
                        definition = desc[method.path][method.uname]
                        structure += f"def {entity.name}() -> {definition}\n"
                    else:
                        structure += f"def {entity.name}()\n"
            structures.append(structure)
        return structures

    def get_modules_paths(self):
        paths = []
        for path in self._get_paths_recursively(self.base_dir):
            paths.append(path)
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
