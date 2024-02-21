import logging
import ast
import os

from pydantic import BaseModel, PrivateAttr
from collections import defaultdict

from codedoc.llm import Llm
from codedoc.prompts import (
    functions_desc_prompts, 
    classes_desc_prompts, 
    modules_desc_prompts, 
    modules_deps_desc_prompts,
    project_overview_prompt
)
from codedoc.parser import Parser

logging.basicConfig(level=logging.INFO)


class Descriptions(BaseModel):
    entities: dict = defaultdict(dict)
    functions: dict = defaultdict(dict)
    classes: dict = defaultdict(dict)
    modules: dict = defaultdict(dict)
    modules_deps: dict = defaultdict(dict)
    project: str = ""

class RepoProcessor(BaseModel):
    parse_structure: bool = False
    use_descriptions: bool = False
    add_dependencies: bool = True
    create_graphs: bool = True
    llm: Llm = Llm()
    parser: Parser = Parser()
    _descriptions: Descriptions = PrivateAttr(Descriptions())

    def get_descriptions(self, attr: str = None):
        if attr is None:
            return self._descriptions
        else:
            return getattr(self._descriptions, attr)

    def generate_documentation(self):
        if self.use_descriptions:
            self.generate_functions_desc()
        self.generate_classes_desc()
        self.generate_modules_desc()
        self.generate_modules_deps_desc()
        self.generate_project_desc()
        self.write_markdown()

    def generate_functions_desc(self, module_path: str = None):
        functions_code = self.parser.get_functions(module_path, attr="code")
        prompts = functions_desc_prompts(functions_code)
        responses = self.llm.run_batch_completions(**prompts, timeout=10, stream=True)
        functions = self.parser.get_functions(module_path)
        for function, response in zip(functions, responses):
            self._descriptions.entities[function.path][function.uname] = response["content"]
            self._descriptions.functions[function.path][function.uname] = response["content"]
    
    def generate_classes_desc(self, module_path: str = None):
        classes = self.parser.get_classes(module_path)
        classes_code = self.get_classes_code(classes)
        prompts = classes_desc_prompts(classes_code)
        responses = self.llm.run_batch_completions(**prompts, timeout=10, stream=True)
        for class_, response in zip(classes, responses):
            self._descriptions.entities[class_.path][class_.name] = response["content"]
            self._descriptions.classes[class_.path][class_.name] = response["content"]
    
    def get_classes_code(self, classes):
        classes_code = []
        for class_ in classes:
            if self.parse_structure:
                if self.use_descriptions:
                    descriptions = self._descriptions.entities[class_.path]
                else:
                    descriptions = None
                code = self.parser.get_code_structure(class_, descriptions=descriptions)
            else:
                code = ast.unparse(class_.node)
            classes_code.append(code)
        return classes_code
    
    def generate_modules_desc(self, module_path: str = None):
        modules = self.parser.get_modules(module_path)
        modules_code = self.get_modules_code(modules)
        prompts = modules_desc_prompts(modules_code)
        responses = self.llm.run_batch_completions(**prompts, timeout=10, stream=True)
        for module, response in zip(modules, responses):
            self._descriptions.modules[module.path] = response["content"]
    
    def get_modules_code(self, modules):
        modules_code = []
        for module in modules:
            if self.parse_structure:
                if self.use_descriptions:
                    descriptions = self._descriptions.entities[module.path]
                else:
                    descriptions = None
                code = self.parser.get_code_structure(module, descriptions=descriptions)
            else:
                code = ast.unparse(module.node)
            if self.create_graphs:
                self.parser.write_graphs(module)
            modules_code.append(code)
        return modules_code
    
    def generate_modules_deps_desc(self, module_path: str = None):
        modules = self.parser.get_modules(module_path)
        modules_paths, modules_code, deps_code, execution_graphs = [], [], [], []
        for module in modules:
            deps = self.parser.get_module_deps(module.path)
            if any(deps):
                module_code, dep_code, execution_graph = self.parser.get_deps_code(module, deps, self.create_graphs)
                if execution_graph != "":
                    modules_code.append(module_code)
                    deps_code.append(dep_code)
                    execution_graphs.append(execution_graph)
                    modules_paths.append(module.path)
                else:
                    self._descriptions.modules_deps[module.path] = "No dependencies with other modules."
            else:
                self._descriptions.modules_deps[module.path] = "No dependencies with other modules."
        prompts = modules_deps_desc_prompts(modules_code, deps_code, execution_graphs)
        responses = self.llm.run_batch_completions(**prompts, timeout=10, stream=True)
        for module_path, response in zip(modules_paths, responses):
            self._descriptions.modules_deps[module_path] = response["content"]
    
    def generate_project_desc(self):
        modules_docu = self.get_modules_descriptions()
        prompt = project_overview_prompt(modules_docu, self.parser.get_tree())
        response = self.llm.run_completions(**prompt, timeout=10, stream=True)
        self._descriptions.project = response["content"]
    
    def get_modules_descriptions(self):
        modules_docu = ""
        if self.add_dependencies:
            for module_path in self._descriptions.modules.keys():
                module_desc = self._descriptions.modules[module_path]
                module_deps_desc = self._descriptions.modules_deps[module_path]
                modules_docu += f"\n\n**Module {module_path}**:\n\n\tDescription:\n\t{module_desc}\n\n\tDependencies with other modules:\n\t{module_deps_desc}\n"
        else:
            for module_path, module_desc in self._descriptions.modules.items():
                modules_docu += f"\n\n**Module {module_path}**:\n\n\tDescription:\n\t{module_desc}\n"
        return modules_docu
    
    def get_classes_descriptions(self):
        classes_docu = ""
        for class_path, class_ in self._descriptions.classes.items():
            for class_name, class_desc in class_.items():
                classes_docu += f"\n**class {class_name} [{class_path}]**:\n\n\t{class_desc}\n"
        return classes_docu

    def write_markdown(self):
        md = self.generate_markdown()
        with open("project.md", "w") as f:
            f.write(md)
    
    def generate_markdown(self):
        md = "# PROJECT OVERVIEW\n\n"
        md += f"{self.get_descriptions('project')}\n\n"

        md += "## PROJECT STRUCTURE\n\n"
        md += f"```\n{self.parser.get_tree()}```\n\n"

        md += "## MODULES"
        md += self.get_modules_descriptions()

        md += "\n\n## CLASSES\n"
        md += self.get_classes_descriptions()
        
        md += "\n\n## EXECUTION FLOWS\n"
        
        md += "\n### MODULES\n"
        for module in self.parser.get_modules_paths():
            file_path = f'./docs/graphs/{os.path.splitext(module)[0]}.png'
            if os.path.exists(file_path):
                md += f"\n![Alt text]({file_path})\n"
        
        md += "\n### DEPENDENCIES\n"
        for module in self.parser.get_modules_paths():
            file_path = f'./docs/graphs/{os.path.splitext(module)[0]}_deps.png'
            if os.path.exists(file_path):
                md += f"\n![Alt text]({file_path})\n"
        return md

if __name__ == "__main__":
    processor = RepoProcessor(
        parser={"base_dir": "./src/codedoc"}
    )
    # processor.generate_functions_desc(module_path="./src/codedoc/process.py")
    # processor.generate_classes_desc(module_path="process.py")
    processor.generate_modules_desc()
    processor.generate_modules_deps_desc()
    print(processor._descriptions.modules_deps)
    # processor.generate_project_desc()
#     # res = functions_desc_args(processor, "./src/codedoc/process.py")
#     asyncio.run(processor._generate_documentation())
#     processor._descriptions
