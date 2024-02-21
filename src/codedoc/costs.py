import ast
import tiktoken
from codedoc.docgen import DocGen

MODEL_INFO = {
    "gpt-4-1106-preview": {"context": 128192, "inprice": 0.01, "outprice": 0.03},
    "gpt-4": {"context": 8192, "inprice": 0.03, "outprice": 0.06},
    "gpt-4-0613": {"context": 8192, "inprice": 0.03, "outprice": 0.06},
    "gpt-4-32k": {"context": 32000, "inprice": 0.06, "outprice": 0.12},
    "gpt-4-32k-0613": {"context": 32000, "inprice": 0.06, "outprice": 0.12},
    "gpt-3.5-turbo-1106": {"context": 16385, "inprice": 0.0010, "outprice": 0.0020},
    "gpt-3.5-turbo-instruct": {"context": 4096, "inprice": 0.0015, "outprice": 0.0020},
    "gpt-3.5-turbo": {"context": 4096, "inprice": 0.0015, "outprice": 0.0020},
    "gpt-3.5-turbo-0613": {"context": 4096, "inprice": 0.0015, "outprice": 0.0020},
    "gpt-3.5-turbo-16k": {"context": 16385, "inprice": 0.0030, "outprice": 0.0040},
    "gpt-3.5-turbo-16k-0613": {"context": 16385, "inprice": 0.0030, "outprice": 0.0040},
}


def calculate_cost(intokens, outtokens, model):
    return round(
        (
            intokens * MODEL_INFO[model]["inprice"]
            + outtokens * MODEL_INFO[model]["outprice"]
        )
        / 1000,
        8,
    )


def count_tokens(text: str, model: str):
    encoding = tiktoken.encoding_for_model(model)
    return len(encoding.encode(text))


def estimate_cost(docgen: DocGen):
    cost = 0
    # estimate functions descriptions costs
    if docgen.use_structure:
        functions_code = docgen.parser.get_functions(attr="code")
        for function_code in functions_code:
            cost += calculate_cost(
                intokens=count_tokens(function_code, docgen.model), outtokens=10, model=docgen.model
            )
    # estimate classes descriptions costs
    docgen._descriptions.entities = None
    for class_ in docgen.parser.get_classes():
        if docgen.use_structure:
            class_code = docgen.parser.get_code_structure(class_)
        else:
            class_code = ast.unparse(class_.node)      
        cost += calculate_cost(
            intokens=count_tokens(class_code, docgen.model), outtokens=10, model=docgen.model
        )
    # estimate modules descriptions costs
    for module in docgen.parser.get_modules():
        if docgen.use_structure:
            module_code = docgen.parser.get_code_structure(module)
        else:
            module_code = ast.unparse(module.node)      
        cost += calculate_cost(
            intokens=count_tokens(module_code, docgen.model), outtokens=50, model=docgen.model
        )
    # estimate modules dependencies descriptions costs
    modules = docgen.parser.get_modules()
    for module in modules:
        deps = docgen.parser.get_module_deps(module.path)
        if any(deps):
            module_code, dep_code, execution_graph = docgen.parser.get_deps_code(module, deps, docgen.output_dir)
            if execution_graph != "":
                intokens = count_tokens(
                    module_code+dep_code+execution_graph, docgen.model
                )
                cost += calculate_cost(
                    intokens=intokens, outtokens=50, model=docgen.model
                )
    # estimate project description costs
    intokens = len(docgen.parser.get_modules_paths()) * 100 # assuming 100 tokens description length per module
    cost += calculate_cost(
        intokens=intokens, outtokens=50, model=docgen.model
    )
    return cost


# if __name__ == "__main__":
#     docgen = DocGen(parser={"base_dir":"./src/codedoc"})
#     print(estimate_cost(docgen))
