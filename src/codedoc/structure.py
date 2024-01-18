from codeas.codebase import Codebase
import json
import os

cb = Codebase(base_dir="../codeas")

with open("repo_map.json", "r") as f:
    repo_map = json.load(f)

def get_function_signature(path, node, include_args=False):
    with open(path, "r") as f:
        lines = f.readlines()

    identifier = get_identifier(node)
    
    if include_args:
        NotImplementedError()
    else:
        return lines[identifier.start_point[0]][:identifier.end_point[1]]

def get_absolute_path(path):
    return os.path.abspath(path)

def get_name(node):
    identifier = get_identifier(node)
    return identifier.text.decode()

def get_identifier(node):
    for child in node.children:
        if child.type == "identifier":
            return child
        
def get_description(path, node):
    id_ = get_name(node) + "_" + str(node.start_point[0])
    return repo_map[get_absolute_path(path)][id_]["short_desc"]
        
def get_file_structure(path, add_description=True):
    root_node =cb.parse_root_node(path)
    file_structure = ""
    for child in root_node.children:
        if child.type == "function_definition":
            file_structure += get_function_signature(path, child) 
            if add_description:
                file_structure += "():\n\t... # " + get_description(path, child) + "\n"
            else:
                file_structure += "():\n\t...\n"
        elif child.type == "class_definition":
            file_structure += get_function_signature(path, child) + "():\n"
            for grandchild in child.children[-1].children: #children[-1] is the class block
                if grandchild.type == "function_definition":
                    file_structure += get_function_signature(path, grandchild)
                    if add_description:
                        file_structure += "():\n\t... # " + get_description(path, grandchild) + "\n"
                    else:
                        file_structure += "():\n\t...\n"
    return file_structure

if __name__ == "__main__":
    file_struc = get_file_structure("../codeas/src/codeas/thread.py")
    print(file_struc)