from codedoc.docgen import DocGen

docgen = DocGen(parser={"base_dir": "src/codedoc"})
docgen.generate_documentation()
