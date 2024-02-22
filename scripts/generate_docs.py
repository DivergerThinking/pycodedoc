import argparse

import toml

from pycodedoc.costs import estimate_cost
from pycodedoc.docgen import DocGen


def main(
    dir_path: str,
    prompts_path: str,
    output_path: str,
    use_structure: bool,
    ignore_relations: bool,
    ignore_graphs: bool,
    model: str,
    estimate: bool,
):
    if prompts_path:
        with open(prompts_path, "r") as f:
            prompts = toml.load(f)
        docgen = DocGen(
            parser={"base_dir": dir_path},
            prompts=prompts,
            use_structure=use_structure,
            add_relations=not ignore_relations,
            create_graphs=not ignore_graphs,
            output_path=output_path,
            model=model,
        )
    else:
        docgen = DocGen(
            parser={"base_dir": dir_path},
            use_structure=use_structure,
            add_relations=not ignore_relations,
            create_graphs=not ignore_graphs,
            output_path=output_path,
            model=model,
        )
    if estimate:
        print(
            f"Estimated cost of generating the documentation: ${estimate_cost(docgen)}"
        )
    else:
        docgen.generate_documentation()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate documentation.")
    parser.add_argument(
        "-d",
        "--dir",
        type=str,
        required=True,
        help="The path of the directory to document",
    )
    parser.add_argument(
        "-p", "--prompts", type=str, help="The path of the prompts file"
    )
    parser.add_argument(
        "-o",
        "--output",
        type=str,
        default="./project.md",
        help="The path of the output file",
    )
    parser.add_argument(
        "-us",
        "--use_structure",
        action="store_true",
        help="Use the structure of the code to generate the documentation",
    )
    parser.add_argument(
        "-ir",
        "--ignore_relations",
        action="store_true",
        help="Add description of the relationship between modules",
    )
    parser.add_argument(
        "-ig",
        "--ignore_graphs",
        action="store_true",
        help="Create execution graphs of the code",
    )
    parser.add_argument(
        "-m",
        "--model",
        type=str,
        default="gpt-3.5-turbo-1106",
        help="The OpenAI model to use for generating the documentation",
    )
    parser.add_argument(
        "-e",
        "--estimate",
        action="store_true",
        help="Prints estimation cost of generating the documentation",
    )
    args = parser.parse_args()
    main(
        args.dir,
        args.prompts,
        args.output,
        args.use_structure,
        args.ignore_relations,
        args.ignore_graphs,
        args.model,
        args.estimate,
    )
