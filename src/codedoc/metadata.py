from codeas import codebase
from openai import OpenAI
import os

client = OpenAI()
cb = codebase.Codebase()

def generate_function_metadata():
    metadata = []
    
    for path in cb.get_modules_paths():
        for function in cb.get_functions(path):
            prompt = """
            Explain in MAXIMUM 10 TOKENS what the following function does:
            """
            prompt += function.content

            response = client.chat.completions.create(
            model="gpt-3.5-turbo-1106",
            messages=[
                {"role": "user", "content": prompt}
            ]
            )
            metadata.append(
            {
                "path": path, 
                "function": function.name, 
                "code": function.content, 
                "response": response.choices[0].message.content}
            )

def get_absolute_path(path):
    return os.path.abspath(path)
      
def convert_to_repo_map(metadata):
    lines = []

    for path in cb.get_modules_paths():
        for function in cb.get_functions(path):
            lines.append(function.node.start_point[0])
    
    repo_map = {}
    for function, line in zip(metadata, lines):
        id_ = function["function"] + "_" + str(line)
        if function["path"] not in repo_map:
            repo_map[get_absolute_path(function["path"])] = {
                id_: {
                    "name": function["function"],
                    "line": line,
                    "type": "function_definition",
                    "short_desc": function["response"]
                }
            }
        else:
            repo_map[get_absolute_path(function["path"])][id_] = {
                "name": function["function"],
                "line": line,
                "type": "function_definition",
                "short_desc": function["response"]
            }

