import argparse
from codedoc.docgen import DocGen
import toml

def main(dir_path: str, prompts_path: str):
    if prompts_path:
        with open(prompts_path, "r") as f:
            prompts = toml.load(f)
        docgen = DocGen(parser={"base_dir": dir_path}, prompts=prompts)
    else:
        docgen = DocGen(parser={"base_dir": dir_path})
    print(docgen.prompts)
    # docgen.generate_documentation()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Generate documentation.')
    parser.add_argument('--dir', type=str, required=True,
                        help='The path of the directory to document')
    parser.add_argument('--prompts', type=str,
                        help='The path of the prompts file')
    args = parser.parse_args()
    main(args.dir, args.prompts)