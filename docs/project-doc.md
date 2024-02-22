# PROJECT OVERVIEW

## Project Overview

The project is a comprehensive documentation generation tool for software projects, aimed at automating the process of creating detailed documentation for functions, classes, modules, dependencies, and project structures. It leverages various modules and technologies to streamline the documentation generation process.

### Core Functionalities:

1. **Automated Documentation Generation**: The project automates the creation of documentation by generating descriptions for functions, classes, modules, and their relationships.

2. **Code Parsing and Analysis**: It parses Python code files to extract function and class definitions, handle dependencies between modules, and generate visualization graphs for code flows.

3. **Prompt Generation**: The project generates prompts to efficiently document functions, classes, modules, and project structure, providing users with formatted instructions and code snippets.

4. **Interaction with OpenAI Models**: Utilizes OpenAI's models for running completions synchronously and asynchronously in batches, handling retries, parsing responses, and processing streaming data for chat applications.

5. **Command-Line Interface**: The project offers a command-line interface tool for configuring documentation options, such as creating graphs, documenting relations and classes, and selecting the OpenAI model for documentation generation.

6. **Cost Estimation**: Calculates the estimated cost of tokenizing and processing code structures based on a given model's pricing scheme, enabling users to estimate the costs associated with generating documentation.

### Use Cases:

1. **Automatic Documentation Generation**: Developers can use the tool to automatically generate detailed documentation for their codebase without the need for manual intervention.

2. **Efficient Documentation**: By providing prompts and guidelines, the tool helps users efficiently document functions, classes, modules, and project structures.

3. **Cost Analysis**: Users can estimate the costs associated with generating documentation based on the code structure and the selected OpenAI model.

4. **Improved Collaboration**: With comprehensive documentation, team members can better understand code functionalities, dependencies, and project structures, leading to improved collaboration and code maintenance.

Overall, the project aims to enhance the documentation process for software projects by providing automation, efficiency, and cost estimation capabilities.

## PROJECT STRUCTURE

```
├── llm.py
├── docgen.py
├── prompts.py
├── parser.py
├── cli.py
├── utils.py
└── costs.py
```

## MODULES

**Module llm.py**:

Description:
This module facilitates running completions synchronously and asynchronously in batches using OpenAI's models, handling retries and parsing responses, including processing streaming data for chat applications.


**Module docgen.py**:

Description:
This module generates documentation for a software project by automatically creating descriptions for functions, classes, modules, and their relationships. It uses Pydantic for model definitions and a language model for content generation based on predefined prompts. The final output is written in Markdown format, including an overview of the project structure and optional visual graphs.

Relations with other modules:
The `DocGen` module interacts with other modules as follows:
- `generate_functions_desc()` calls `parser.py` to get functions and `prompts.py` for function prompts, then uses `llm.py` for batch completions.
- `generate_classes_desc()` interacts with `parser.py` for classes and `prompts.py` for class prompts, using `llm.py` for completions.
- `generate_modules_desc()` communicates with `parser.py` to fetch modules and `prompts.py` for module prompts, utilizing `llm.py` for completions.
- `generate_modules_deps_desc()` involves `parser.py` for modules and dependencies, `prompts.py` for prompts, and `llm.py` for completions.
- `get_tree()` in `parser.py` is called by `generate_project_desc()` to generate the project overview.


**Module prompts.py**:

Description:
This module generates prompts for documenting functions, classes, modules, their dependencies, and project structure. It formats instructions and code snippets for users to create documentation efficiently.


**Module parser.py**:

Description:
This module parses Python code files to extract function and class definitions, and their structure. It also handles dependencies between modules, generates code structure, and visualization graphs for code flows.

Relations with other modules:
The `parser.py` module globally interacts with the `utils.py` module by calling the function `set_logger()` whenever logging functionality is required. This function sets up a logger with specific configurations using the `RichHandler` from the `rich.logging` module.


**Module cli.py**:

Description:
This module defines a command-line interface tool for generating documentation for a codebase. It allows configuring various documentation options such as creating graphs, documenting relations and classes, and choosing an OpenAI model for documentation generation.

Relations with other modules:
The `main` function in `cli.py` interacts with the `generate_documentation` method in `docgen.py` from the `pycodedoc.docgen` module. Additionally, it interacts with the `estimate_cost` function in `costs.py` from the `pycodedoc.costs` module.


**Module utils.py**:

Description:
This module sets up a logger for the application with a rich output format including timestamps, log levels, and messages. It prevents logs from propagating to parent loggers and ensures only one rich handler is used.


**Module costs.py**:

Description:
Calculates the estimated cost of tokenizing and processing code structures based on a given model's pricing scheme. Includes functions to count tokens, analyze code structures, and calculate costs for functions, classes, modules, and their dependencies.


## CLASSES

**class Llm [llm.py]**:

Runs GPT-3 completions synchronously/asynchronously by batch, parsing responses.

**class Descriptions [docgen.py]**:

Manages entities, functions, classes, modules, and project information.

**class DocGen [docgen.py]**:

Generates detailed documentation for project modules, classes, and relationships.

**class Function [parser.py]**:

Represents a function with name, path, code, and node.

**class Class [parser.py]**:

Class representing a code class with its methods.

**class Module [parser.py]**:

Processes code entities from a file into class or function objects.

**class Parser [parser.py]**:

Parses Python code structures and dependencies for analysis and visualization.
