
import ast
import importlib
import types
from codedoc.utils import read_file

class ImportPathVisitor(ast.NodeVisitor):
    def __init__(self):
        self.module_paths = set()

    def visit_ImportFrom(self, node):
        for entity in self.get_entities(node):
            if isinstance(entity, types.ModuleType):
                self.module_paths.add(entity.__file__)
            else:
                self.module_paths.add(importlib.import_module(entity.__module__).__file__)
    
    def get_entities(self, node):
        module = importlib.import_module(node.module)
        for name in self.get_names(node):
            if hasattr(module, name):
                yield getattr(module, name)
    
    def get_names(self, node):
        for name in node.names:
            if name.asname is not None:
                yield name.asname
            else:
                yield name.name

if __name__ == "__main__":
    python_code = read_file("./src/codedoc/process.py")
    tree = ast.parse(python_code)

    visitor = ImportPathVisitor()
    visitor.visit(tree)
    for path in visitor.module_paths:
        print(path)
