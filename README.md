# pycodedoc

Welcome to pycodedoc, a Python tool leveraging generative AI to effortlessly document your Python projects.

#### 📚 AI-Generated Documentation
Uses LLMs to automatically generate markdown documentation containing:
- an overview of the project as a whole, its main functionalities and its structure
- descriptions of the modules used in your project and how they interact with each other
- descriptions of the classes used throughout your project
- graphs showing the execution flow of your code

#### 💻 CLI tool
The CLI tool allows you to easily:
- modify the prompts you want to use for documenting your project
- use the OpenAI model of your choice
- estimate the costs of generating the documentation beforehand

#### 🐍 Python API
The library's API enables you to build on top of the tool

##  🛠️ Installation

The easiest way to install the tool is by using Pip:

```bash
pip install pycodedoc
```

Alternatively, you can clone the repository and install the package in editable mode (best for development):

```bash
git clone ...
cd pycodedoc
pip install -e .
```

#### Graphviz

To generate graphs showing the execution flows of your code we are using the [code2flow](https://github.com/scottrogowski/code2flow) python library which requires having graphviz. You can follow their documentation for installing the library on your corresponding OS: https://graphviz.org/download/, even though another very simple OS-free way of doing is to install it using conda: 

```bash
conda install graphviz
```

If you don't want to visualize your code's execution flow, you can ignore this step.

#### OpenAI key

Currently, the tool only supports OpenAI as a provider. To add your OpenAI key, export it as an environment variable via the terminal:

```bash
export OPENAI_API_KEY="..."
```

## 💻 CLI Usage

| Options           | Description                                                                                           |
|-------------------|-------------------------------------------------------------------------------------------------------|
| `--base-dir` or `-d`   | The directory of the Python project you want to document.                                             |
| `--output-dir` or `-o` | The output directory path. Default is "docs/".                                               |
| `--model` or `-m` | The OpenAI model to use for generating the documentation. Default is "gpt-3.5-turbo-0125".           |
| `--estimate` or `-e` | Prints estimation cost of generating the documentation. Default is False.                            |
| `--configure` or `-c` | Writes the defaults prompts to a prompt.toml file which can be modified. Default is False.                            |
| `--use-structure` or `-us` | Use the structure of the code to generate the documentation. Default is False.                      |
| `--no-relations` or `-nr` | Does not generate relationship between modules. Default is False.                             |
| `--no-classes` or `-nc` | Does not generate classes descriptions. Default is False.                                              |

### Project directory

To run the tool you must specify the directory where your python project is found. Ideally, all of your modules are stored in a single directory (ex. src/ directory). Here is an example on document the `pycodedoc` project itself.

```bash
pycodedoc -d src/codedoc
```

This will write the output to a markdown file under "./docs/project-doc.md". </br>
**NOTE**: Only Python files are used for documenting the project. 

### 💲 Cost of running the tool

The cost of running the tool largely varies based on the size of the codebase and the model you use. To avoid bad surprises, you can first estimate the cost of running the tool by using the ``--estimate`` option:

```bash
pycodedoc -d src/codedoc --estimate
```

Running the tool on the ./src/pycodedoc/ directory approximately costs $0.01 if using the default configuration.

### 🤖 Selecting a specific model

By default, the tool uses the latest ``gpt-3.5-turbo-0125`` model since it is currently the cheapest capable chat model from OpenAI.
You can however use another model by passing the model parameter using the ``--model`` or `-m` option

```bash
pycodedoc -d src/codedoc -m gpt-4-0125-preview
```

### 🔖 Configuring prompts

The prompts used for documenting your codebase can be accessed and modified by using the `--configure` or `-c` option.

```bash
pycodedoc --configure
```

### 📂 Output directory

By default, the documentation is stored under the /docs directory. If this directory is already in use and you want to avoid using it, you can modify the output directory with the `--output-dir` or `-o` option

```bash
pycodedoc -d src/codedoc --o project_docs
```

### 💾 Using code structure

Instead of using the entire modules' content, you can only use the structure of the code (imports, signatures and function descriptions) via the `--use-structure` option. This is particularly useful if you have large files whose content may exceed the model's context window maximum token limit.

```bash
pycodedoc -d src/codedoc --use-structure
```

**NOTE**: the descriptions for each function in the files will be generated beforehand to make the code structure more meaningful while keeping the file's token count low. The cost of this process is (more or less) offset by the reduction in tokens from the resulting code structure.

### 🔽 Reducing the documentation process

You can also reduce the documentation process by NOT generating descriptions for the classes or modules' relationships using the `--no-classes` and `--no-relations` options. 

```bash
pycodedoc -d src/codedoc --no-classes --no-relations
```

This reduces the overall context passed to the LLMs, reducing costs and speeding up the generation process. 

## 🐍 API Usage

You can build on top of the tool by using the main functions from the API.

#### Generating documentation (same as running `pycodedoc` from CLI)

```python
from pycodedoc import DocGen

docgen = DocGen(base_dir="src/pycodedoc")
docgen.generate_documentation()
```

#### Generating descriptions for part of the codebase

```python
from pycodedoc import DocGen

docgen = DocGen(base_dir="src/pycodedoc") # other configurations are the same as in CLI
docgen.generate_descriptions("functions")
# OUTPUT -> list of descriptions for each function in the project
docgen.generate_descriptions("functions", module_path="parser.py")
# OUTPUT -> list of descriptions for the functions inside the parser.py module
docgen.generate_descriptions("classes")
# OUTPUT -> list of descriptions for each classes in the project
docgen.generate_descriptions("classes", module_path="parser.py")
# OUTPUT -> list of descriptions for the classes inside the parser.py module
docgen.generate_descriptions("modules")
# OUTPUT -> list of descriptions for each modules in the project
docgen.generate_descriptions("modules_relations")
# OUTPUT -> list of descriptions for each classes in the project
docgen.generate_descriptions("project")
# OUTPUT -> project description [str]. NOTE: first need to generate modules descriptions
```

