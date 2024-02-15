import tiktoken
from codedoc.parser import Parser

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


def calc_cost(intokens, outtokens, model):
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


def estimate_cost(cb, model):
    cost = 0
    # for path in cb.get_modules_paths():
    #     for function in cb.get_functions(path):
    #         cost += calc_cost(
    #             intokens=count_tokens(function.content, model),
    #             outtokens=10,
    #             model=model,
    #         )
    return cost


if __name__ == "__main__":
    parser = Parser()
    print(estimate_cost(parser, model="gpt-3.5-turbo-instruct"))
