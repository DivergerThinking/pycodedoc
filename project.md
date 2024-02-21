# PROJECT OVERVIEW

## Project Overview

The project encompasses a suite of modules designed to facilitate the understanding and documentation of software projects through automated analysis, parsing, and generation of documentation. The modules cover a wide range of functionalities, including parsing and extracting code structures and dependencies, running completions for documentation generation, and estimating the cost of text processing using GPT models.

### Core Functionalities
1. **deps.py**: Provides functionality to parse, extract, and manipulate dependencies and code structures from source files. This includes obtaining nodes and edges relevant to a set of files, building execution graphs, and identifying cross-file dependencies.

2. **llm.py**: Offers a class for running completions synchronously and asynchronously, utilizing OpenAI's `chat.completions` API to generate responses and providing methods for parsing and aggregating the results.

3. **docgen.py**: Responsible for automatically generating documentation for the software project. It includes prompts and completions to create descriptions for functions, classes, modules, and their dependencies, as well as generating an overview of the project, its structure, and execution flows.

4. **prompts.py**: Provides functions to generate prompts for documenting different parts of a codebase, including functions, classes, and modules, with specific instructions and contextual code snippets.

5. **parser.py**: Handles parsing and analyzing Python code files within a given directory, extracting and representing the structure of classes and functions, capturing dependencies between modules, and generating execution flow diagrams.

6. **costs.py**: Estimation of the cost of using different GPT models for text processing, including calculating the cost based on input and output tokens and counting tokens in the input text based on a specified model's encoding.

### Use Cases
- Automated generation of documentation for functions, classes, and modules.
- Parsing and visualization of code structures and dependencies.
- Estimation of GPT model processing costs for text generation.

The project's modules collectively aim to streamline the process of understanding, documenting, and analyzing software codebases, enhancing developer productivity and codebase comprehension.

## PROJECT STRUCTURE

```
├── deps.py
├── llm.py
├── docgen.py
├── prompts.py
├── parser.py
└── costs.py
```

## MODULES

**Module deps.py**:

	Description:
	This module provides functionality to parse, extract, and manipulate dependencies and code structures from source files. It allows for obtaining nodes and edges relevant to a set of files, trimming dependencies, building execution graphs, and identifying cross-file dependencies. Additionally, it facilitates the extraction of dependency-related code from the base file. The module leverages AST parsing and graph manipulation to achieve these functionalities.

	Dependencies with other modules:
	No dependencies with other modules.


**Module llm.py**:

	Description:
	This module provides a `Llm` class for running completions synchronously and asynchronously. It handles both single and batch requests, and supports retries with logging. The class uses OpenAI's `chat.completions` API to generate responses and provides methods for parsing and aggregating the results.

	Dependencies with other modules:
	No dependencies with other modules.


**Module docgen.py**:

	Description:
	This module, `DocGen`, is responsible for generating documentation for a software project. It uses various prompts and completions to automatically create descriptions for functions, classes, modules, and their dependencies. The generated documentation includes an overview of the project, its structure, modules and classes descriptions, as well as execution flows and graphs.

	Dependencies with other modules:
	### Concise Function Descriptions:

1. `generate_functions_desc`: Generate descriptions for functions using AI completions.
2. `generate_classes_desc`: Generate descriptions for classes using AI completions.
3. `generate_modules_desc`: Generate descriptions for modules using AI completions.
4. `generate_modules_deps_desc`: Generate descriptions for module dependencies using AI completions.
5. `generate_project_desc`: Generate description for the project using AI completions.
6. `generate_markdown`: Generate Markdown documentation for the project structure.


**Module prompts.py**:

	Description:
	This module provides functions to generate prompts for documenting different parts of a codebase. The `get_functions_prompts` function generates prompts for documenting functions, `get_classes_prompts` for documenting classes, and `get_modules_prompts` for documenting modules. The prompts include specific instructions and contextual code snippets.

	Dependencies with other modules:
	No dependencies with other modules.


**Module parser.py**:

	Description:
	This module is responsible for parsing and analyzing Python code files within a given directory. It provides functionality to extract and represent the structure of the classes and functions of the code, and also captures the dependencies between modules. Additionally, it can manipulate the code structure and generate execution flow diagrams.

	Dependencies with other modules:
	The function `parse_files` parses groups, nodes, and edges from the files.


**Module costs.py**:

	Description:
	This module provides functionality for estimating the cost of using different GPT models for text processing. It includes functions to calculate the cost based on the number of input and output tokens, as well as to count the tokens in the input text based on the specified model's encoding. The `estimate_cost` function is meant to be used to estimate the cost for a given model and input text.

	Dependencies with other modules:
	No dependencies with other modules.


## CLASSES

**class DepsParser [deps.py]**:

	This class analyzes and extracts dependencies from code using AST.

**class Llm [llm.py]**:

	This class facilitates synchronous and asynchronous completions with OpenAI's API.

**class Descriptions [docgen.py]**:

	This class stores information about entities, functions, classes, modules, and dependencies.

**class DocGen [docgen.py]**:

	This class generates documentation for a codebase, including functions, classes, modules, and project overview.

**class Function [parser.py]**:

	This class represents a function with its attributes and properties.

**class Class [parser.py]**:

	This class represents a code class with methods and parsing capabilities.

**class Module [parser.py]**:

	This class represents a module with functions and classes.

**class Parser [parser.py]**:

	This class provides methods to parse and analyze Python code.


## EXECUTION FLOWS

### MODULES

![Alt text](./docs/graphs/deps.png)

![Alt text](./docs/graphs/llm.png)

![Alt text](./docs/graphs/docgen.png)

![Alt text](./docs/graphs/parser.png)

![Alt text](./docs/graphs/costs.png)

### DEPENDENCIES

![Alt text](./docs/graphs/docgen_deps.png)

![Alt text](./docs/graphs/parser_deps.png)
