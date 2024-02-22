import os

import toml
import typer

from pycodedoc.costs import estimate_cost
from pycodedoc.docgen import DocGen

app = typer.Typer()


def load_prompts(prompts_path: str):
    with open(prompts_path, "r") as f:
        prompts = toml.load(f)
    return prompts


def write_prompts(content: str, path: str):
    with open(path, "w") as f:
        toml.dump(content, f)


@app.command()
def main(
    base_dir: str = typer.Option(
        "", "--dir", "-d", help="The path of the directory to document"
    ),
    output_dir: str = typer.Option(
        "./docs", "--output", "-o", help="The path of the output file"
    ),
    no_graphs: bool = typer.Option(
        False, "--no-graphs", "-ng", help="Do not create execution graphs of the code"
    ),
    no_relations: bool = typer.Option(
        False,
        "--no-relations",
        "-nr",
        help="Do not document the relations between modules",
    ),
    no_classes: bool = typer.Option(
        False, "--no-classes", "-nc", help="Do not document the classes in the codebase"
    ),
    use_structure: bool = typer.Option(
        False,
        "--use-structure",
        "-us",
        help="Only use the structure of the codebase to generate the documentation",
    ),
    model: str = typer.Option(
        "gpt-3.5-turbo-1106",
        "--model",
        "-m",
        help="The OpenAI model to use for generating the documentation",
    ),
    estimate: bool = typer.Option(
        False,
        "--estimate",
        "-e",
        help="Prints estimation cost of generating the documentation",
    ),
    configure: bool = typer.Option(
        False, "--configure", "-c", help="Configure the prompts file"
    ),
):
    if base_dir == "" and configure is False:
        typer.echo(
            "Please provide a directory to document with the --dir or -d option. Use 'pycodedoc --help' for more information."
        )
        raise typer.Abort()
    if os.path.exists("prompts.toml"):
        prompts = load_prompts("prompts.toml")
        docgen = DocGen(
            parser={"base_dir": base_dir},
            prompts=prompts,
            create_graphs=not no_graphs,
            add_relations=not no_relations,
            add_classes=not no_classes,
            use_structure=use_structure,
            output_dir=output_dir,
            model=model,
        )
    else:
        docgen = DocGen(
            parser={"base_dir": base_dir},
            create_graphs=not no_graphs,
            add_relations=not no_relations,
            add_classes=not no_classes,
            use_structure=use_structure,
            output_dir=output_dir,
            model=model,
        )
    if estimate:
        typer.echo(
            f"Estimated cost of generating the documentation: ${estimate_cost(docgen)}"
        )
    elif configure:
        write_prompts(docgen.prompts, "prompts.toml")
        typer.echo(
            "Prompts file written to prompts.toml. Modify the file as needed and make sure to execute 'pycodedoc' from the same directory as the file."
        )
    else:
        docgen.generate_documentation()


if __name__ == "__main__":
    app()
