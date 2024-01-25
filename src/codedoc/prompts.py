from __future__ import annotations
from codedoc.utils import read_file
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from codedoc.process import RepoProcessor

NUM_TOKENS = {
    "modules_desc": 50,
    "project_desc": 50,
}

MODULE_DESC = """
Write a short documentation explaining what the module does:
{code}.
The paragraph should be at most {num_tokens} tokens long.
""".strip()

def modules_desc_args(processor: RepoProcessor):
    return {
        "prompts_map": {
            MODULE_DESC.format(
                code=read_file(path), num_tokens=NUM_TOKENS["modules_desc"]
            ): path
            for path in processor.codebase.get_modules_paths()
        },
        "max_tokens": int(NUM_TOKENS["modules_desc"]*1.2)
    }
    
PROJECT_OVERVIEW = """
Write a high level overview of the project that encapsulates its use cases and core functionalities.
Try not to go over {num_tokens} tokens.

Project structure:
{tree}

Modules:
{modules}
""".strip()

def project_desc_args(processor: RepoProcessor):
    modules_desc = ""
    for module_path, module_desc in processor._docu["modules_desc"].items():
        modules_desc += f"\t- {module_path}:\n\t\t{module_desc}\n"
    return {
        "prompts_map":
            {
                PROJECT_OVERVIEW.format(
                    modules=modules_desc, 
                    tree=processor.codebase.get_tree(),
                    num_tokens=NUM_TOKENS["project_desc"]
                ): 0
            },
        "max_tokens": int(NUM_TOKENS["project_desc"]*1.2)
    }