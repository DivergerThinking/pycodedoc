import ast
import os

from pydantic import BaseModel, PrivateAttr
from collections import defaultdict

from codedoc.llm import Llm
from codedoc.prompts import (
    get_functions_prompts, 
    get_classes_prompts, 
    get_modules_prompts, 
    get_modules_deps_prompts,
    get_project_prompt,
    PROMPTS
)
from codedoc.parser import Parser

class Descriptions(BaseModel):
    entities: dict = defaultdict(dict)
    functions: dict = defaultdict(dict)
    classes: dict = defaultdict(dict)
    modules: dict = defaultdict(dict)
    modules_deps: dict = defaultdict(dict)
    project: str = ""

class DocGen(BaseModel):
    use_structure: bool = False
    add_relations: bool = True
    create_graphs: bool = True
    prompts: dict = PROMPTS
    output_dir: str = "./docs"
    model: str = "gpt-3.5-turbo-1106"
    llm: Llm = Llm()
    parser: Parser = Parser()
    _descriptions: Descriptions = PrivateAttr(Descriptions())

    def get_descriptions(self, attr: str = None):
        if attr is None:
            return self._descriptions
        else:
            return getattr(self._descriptions, attr)

    def generate_documentation(self):
        if self.use_structure:
            self.generate_functions_desc()
        self.generate_classes_desc()
        self.generate_modules_desc()
        if self.add_relations:
            self.generate_modules_deps_desc()
        self.generate_project_desc()
        self.write_markdown()

    def generate_functions_desc(self, module_path: str = None):
        functions_code = self.parser.get_functions(module_path, attr="code")
        prompts = get_functions_prompts(functions_code, **self.prompts["functions"])
        responses = self.llm.run_batch_completions(**prompts, timeout=10, stream=True, model=self.model)
        functions = self.parser.get_functions(module_path)
        for function, response in zip(functions, responses):
            self._descriptions.entities[function.path][function.uname] = response["content"]
            self._descriptions.functions[function.path][function.uname] = response["content"]
    
    def generate_classes_desc(self, module_path: str = None):
        classes = self.parser.get_classes(module_path)
        classes_code = self.get_classes_code(classes)
        prompts = get_classes_prompts(classes_code, **self.prompts["classes"])
        responses = self.llm.run_batch_completions(**prompts, timeout=10, stream=True, model=self.model)
        for class_, response in zip(classes, responses):
            self._descriptions.entities[class_.path][class_.name] = response["content"]
            self._descriptions.classes[class_.path][class_.name] = response["content"]
    
    def get_classes_code(self, classes):
        classes_code = []
        for class_ in classes:
            if self.use_structure:
                descriptions = self._descriptions.entities[class_.path]
                code = self.parser.get_code_structure(class_, descriptions=descriptions)
            else:
                code = ast.unparse(class_.node)
            classes_code.append(code)
        return classes_code
    
    def generate_modules_desc(self, module_path: str = None):
        modules = self.parser.get_modules(module_path)
        modules_code = self.get_modules_code(modules)
        prompts = get_modules_prompts(modules_code, **self.prompts["modules"])
        responses = self.llm.run_batch_completions(**prompts, timeout=10, stream=True, model=self.model)
        for module, response in zip(modules, responses):
            self._descriptions.modules[module.path] = response["content"]
    
    def get_modules_code(self, modules):
        modules_code = []
        for module in modules:
            if self.use_structure:
                descriptions = self._descriptions.entities[module.path]
                code = self.parser.get_code_structure(module, descriptions=descriptions)
            else:
                code = ast.unparse(module.node)
            if self.create_graphs:
                self.parser.write_graphs(module, self.output_dir)
            modules_code.append(code)
        return modules_code
    
    def generate_modules_deps_desc(self, module_path: str = None):
        modules = self.parser.get_modules(module_path)
        modules_paths, modules_code, deps_code, execution_graphs = [], [], [], []
        for module in modules:
            deps = self.parser.get_module_deps(module.path)
            if any(deps):
                module_code, dep_code, execution_graph = self.parser.get_deps_code(module, deps, self.output_dir, self.create_graphs)
                if execution_graph != "":
                    modules_code.append(module_code)
                    deps_code.append(dep_code)
                    execution_graphs.append(execution_graph)
                    modules_paths.append(module.path)
                else:
                    self._descriptions.modules_deps[module.path] = None
            else:
                self._descriptions.modules_deps[module.path] = None
        prompts = get_modules_deps_prompts(modules_code, deps_code, execution_graphs, **self.prompts["modules_deps"])
        responses = self.llm.run_batch_completions(**prompts, timeout=10, stream=True, model=self.model)
        for module_path, response in zip(modules_paths, responses):
            self._descriptions.modules_deps[module_path] = response["content"]
    
    def generate_project_desc(self):
        modules_docu = self.get_modules_descriptions()
        prompt = get_project_prompt(modules_docu, self.parser.get_tree(), **self.prompts["project"])
        response = self.llm.run_completions(**prompt, timeout=10, stream=True, model=self.model)
        self._descriptions.project = response["content"]
    
    def get_modules_descriptions(self):
        modules_docu = ""
        if self.add_relations:
            for module_path in self._descriptions.modules.keys():
                module_desc = self._descriptions.modules[module_path]
                module_deps_desc = self._descriptions.modules_deps[module_path]
                modules_docu += f"\n\n**Module {module_path}**:\n\nDescription:\n{module_desc}\n"
                if module_deps_desc:
                    modules_docu += f"\nRelations with other modules:\n{module_deps_desc}\n"
        else:
            for module_path, module_desc in self._descriptions.modules.items():
                modules_docu += f"\n\n**Module {module_path}**:\n\nDescription:\n{module_desc}\n"
        return modules_docu
    
    def get_classes_descriptions(self):
        classes_docu = ""
        for class_path, class_ in self._descriptions.classes.items():
            for class_name, class_desc in class_.items():
                classes_docu += f"\n**class {class_name} [{class_path}]**:\n\n{class_desc}\n"
        return classes_docu

    def write_markdown(self):
        md = self.generate_markdown()
        with open(os.path.join(self.output_dir, "project-doc.md"), "w") as f:
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
        
        if self.create_graphs:
            md += "\n\n## EXECUTION FLOWS\n"
            
            md += "\n### MODULES\n"
            for module in self.parser.get_modules_paths():
                file_path = f'{self.output_dir}/graphs/{os.path.splitext(module)[0]}.png'
                if os.path.exists(file_path):
                    rel_path = os.path.relpath(file_path, self.output_dir)
                    md += f"\n![Alt text]({rel_path})\n"
            
            if self.add_relations:
                md += "\n### MODULE RELATIONSHIPS\n"
                for module in self.parser.get_modules_paths():
                    file_path = f'{self.output_dir}/graphs/{os.path.splitext(module)[0]}_deps.png'
                    if os.path.exists(file_path):
                        rel_path = os.path.relpath(file_path, self.output_dir)
                        md += f"\n![Alt text]({rel_path})\n"
        
        return md

if __name__ == "__main__":
    docgen = DocGen(parser= {"base_dir": "./src/codedoc"})
    docgen.generate_documentation()