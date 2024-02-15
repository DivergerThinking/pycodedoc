NUM_TOKENS = {
    "function_desc": 10,
    "classes_desc": 10,
    "modules_desc": 50,
    "modules_deps_desc": 50,
    "project_desc": 50,
}


FUNCTIONS_DESC = """
Write a concised description of what the function does in AT MOST {num_tokens} tokens:
{code}.
"""


def functions_desc_prompts(functions_code: list, **kwargs) -> dict:
    prompts = [
        FUNCTIONS_DESC.format(code=code, num_tokens=NUM_TOKENS["function_desc"])
        for code in functions_code
    ]
    messages_batches = [[{"role":"user", "content": prompt}] for prompt in prompts]
    max_tokens_buffer = int(NUM_TOKENS["function_desc"] * 1.2)
    return {"messages_batches": messages_batches, "max_tokens": max_tokens_buffer}


FUNCTIONS_DESC = """
Write a concised description of what the class does in AT MOST {num_tokens} tokens:
{code}.
"""


def classes_desc_prompts(classes_code: list) -> dict:
    prompts = [
        FUNCTIONS_DESC.format(code=code, num_tokens=NUM_TOKENS["classes_desc"])
        for code in classes_code
    ]
    messages_batches = [[{"role":"user", "content": prompt}] for prompt in prompts]
    max_tokens_buffer = int(NUM_TOKENS["classes_desc"] * 1.2)
    return {"messages_batches": messages_batches, "max_tokens": max_tokens_buffer}


MODULE_DESC = """
Write a short descriptions explaining what this module does:
{code}.
Focus high level overview of the module, not the implementation details like class and function names. 
The description should be at most {num_tokens} tokens long.
""".strip()


def modules_desc_prompts(modules_code: list) -> dict:
    prompts = [
        MODULE_DESC.format(code=code, num_tokens=NUM_TOKENS["modules_desc"])
        for code in modules_code
    ]
    messages_batches = [[{"role":"user", "content": prompt}] for prompt in prompts]
    max_tokens_buffer = int(NUM_TOKENS["modules_desc"] * 1.2)
    return {"messages_batches": messages_batches, "max_tokens": max_tokens_buffer}

MODULE_DEPS_DESC = """
Write a short description on how a given module interacts with other modules it depends on.
Try not to go over {num_tokens} tokens.

### MODULE:

{module_code}

### DEPENDENT MODULES:

{dep_code}

### INTERACTION BETWEEN MODULES:

{execution_graph}

""".strip()


def modules_deps_desc_prompts(modules_code: list, deps_code: list, execution_graphs: list) -> dict:
    prompts = [
        MODULE_DEPS_DESC.format(
            module_code=module_code, 
            dep_code=dep_code,
            execution_graph=execution_graph,
            num_tokens=NUM_TOKENS["modules_deps_desc"],
        )
        for module_code, dep_code, execution_graph in zip(modules_code, deps_code, execution_graphs)
    ]
    messages_batches = [[{"role":"user", "content": prompt}] for prompt in prompts]
    max_tokens_buffer = int(NUM_TOKENS["modules_deps_desc"] * 1.2)
    return {"messages_batches": messages_batches, "max_tokens": max_tokens_buffer}

PROJECT_OVERVIEW = """
Write a high level overview of the project that encapsulates its use cases and core functionalities.
Try not to go over {num_tokens} tokens.

Project structure:
{tree}

Modules:
{modules_docu}
""".strip()

def project_overview_prompt(modules_docu: list, tree: str) -> dict: 
    prompt = PROJECT_OVERVIEW.format(modules_docu=modules_docu, tree=tree, num_tokens=NUM_TOKENS["project_desc"])
    messages = [{"role":"user", "content": prompt}]
    return {"messages": messages, "max_tokens": int(NUM_TOKENS["project_desc"] * 1.2)}
