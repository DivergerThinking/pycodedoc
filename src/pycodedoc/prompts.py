SYSTEM_PROMPT = """
You are a senior software engineer specialised in documenting large complex codebases.
You will be given some instructions as well as the specific part of the codebase to use as context.

""".strip()

PROMPTS = {
    "functions": {
        "instructions": "Write a concise description of what the function does in around 10 words. Only add the description, no titles.",
        "system_prompt": SYSTEM_PROMPT,
    },
    "classes": {
        "instructions": "Write a concise description of what the class does in around 10 words. Only add the description, no titles.",
        "system_prompt": SYSTEM_PROMPT,
    },
    "modules": {
        "instructions": """

Write a short descriptions explaining what this module does in maximum 50 words. Only add the description, no titles. 
Focus on the high level functionality of the module, not the implementation details like class and function names.

""".strip(),
        "system_prompt": SYSTEM_PROMPT,
    },
    "modules_deps": {
        "instructions": """

Write a short description on how a given module interacts with other modules it depends on in maximum 50 words. Only add the description, no titles.
Focus on how the modules are interacting at a high level, not the implementation details such as the specific function calls.

""".strip(),
        "system_prompt": SYSTEM_PROMPT,
    },
    "project": {
        "instructions": """

Write a high level overview of the project that encapsulates its core functionalities.
Do not explain what every module does (this will be added to the documentation separately) but rather what the project as a whole does.

""".strip(),
        "system_prompt": SYSTEM_PROMPT,
    },
}


TEMPLATE_CODE = """
### INSTRUCTIONS: 
{instructions}

### CONTEXT:
{code}
"""


def get_functions_prompts(
    functions_code: list, instructions: str, system_prompt: str
) -> dict:
    prompts = [
        TEMPLATE_CODE.format(code=code, instructions=instructions)
        for code in functions_code
    ]
    messages_batches = [
        [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt},
        ]
        for prompt in prompts
    ]
    return {"messages_batches": messages_batches}


def get_classes_prompts(
    classes_code: list, instructions: str, system_prompt: str
) -> dict:
    prompts = [
        TEMPLATE_CODE.format(code=code, instructions=instructions)
        for code in classes_code
    ]
    messages_batches = [
        [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt},
        ]
        for prompt in prompts
    ]
    return {"messages_batches": messages_batches}


def get_modules_prompts(
    modules_code: list, instructions: str, system_prompt: str
) -> dict:
    prompts = [
        TEMPLATE_CODE.format(code=code, instructions=instructions)
        for code in modules_code
    ]
    messages_batches = [
        [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt},
        ]
        for prompt in prompts
    ]
    return {"messages_batches": messages_batches}


TEMPLATE_CODE_DEPS = """
### INSTRUCTIONS: 
{instructions}

### CONTEXT:

# MODULE:
{module_code}

# DEPENDENT MODULES:
{dep_code}

# INTERACTION BETWEEN MODULES:
{execution_graph}
"""


def get_modules_deps_prompts(
    modules_code: list,
    deps_code: list,
    execution_graphs: list,
    instructions: str,
    system_prompt: str,
) -> dict:
    prompts = [
        TEMPLATE_CODE_DEPS.format(
            module_code=module_code,
            dep_code=dep_code,
            execution_graph=execution_graph,
            instructions=instructions,
        )
        for module_code, dep_code, execution_graph in zip(
            modules_code, deps_code, execution_graphs
        )
    ]
    messages_batches = [
        [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt},
        ]
        for prompt in prompts
    ]
    return {"messages_batches": messages_batches}


TEMPLATE_PROJECT = """
### INSTRUCTIONS:
{instructions}

### CONTEXT:

# MODULES DOCUMENTATION:
{modules_docu}

# PROJECT STRUCTURE:
{tree}
"""


def get_project_prompt(
    modules_docu: list, tree: str, instructions: str, system_prompt: str
) -> dict:
    prompt = TEMPLATE_PROJECT.format(
        modules_docu=modules_docu, tree=tree, instructions=instructions
    )
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": prompt},
    ]
    return {"messages": messages}
