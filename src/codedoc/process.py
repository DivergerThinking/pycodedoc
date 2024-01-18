import asyncio
from pydantic import BaseModel
from tqdm.asyncio import tqdm_asyncio

from codeas.codebase import Codebase
from codedoc.prompts import EXPLAIN
from codedoc.llm import Llm
from codedoc.utils import read_file

class RepoProcessor(BaseModel):
    llm: Llm = Llm()
    use_functions: bool = False
    codebase: Codebase = Codebase()
    
    def generate_descriptions(self):
        if self.use_functions:
            asyncio.run(self.generate_functions_descriptions())

    async def generate_functions_descriptions(self, path: str, max_tokens):
        prompts = [
            EXPLAIN.format(max_tokens=max_tokens, code=function.content) 
            for function in self.codebase.get_functions(path)
        ]
        async for result in self.llm.run_batch_completions(prompts):
            print("RESULT",result.usage)
    
    async def generate_modules_descriptions(self, max_tokens):
        prompts = [
            EXPLAIN.format(max_tokens=max_tokens, code=read_file(path)) 
            for path in self.codebase.get_modules_paths()
        ]
        async for result in self.llm.run_batch_completions(prompts):
            print("RESULT",result.usage)
        
        
if __name__ == "__main__":
    processor = RepoProcessor()
    asyncio.run(
        processor.generate_modules_descriptions(
            # path="../codeas/src/codeas/thread.py", 
            max_tokens=10
        )
    )