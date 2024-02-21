import argparse
from codedoc.docgen import DocGen

def main(dir_path: str):
    docgen = DocGen(parser={"base_dir": dir_path})
    print(docgen.parser.get_modules_paths())
    # docgen.generate_documentation()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Generate documentation.')
    parser.add_argument('--dir', type=str,
                        help='The path of the directory to document')
    args = parser.parse_args()
    main(args.dir)