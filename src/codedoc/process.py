import asyncio
import logging
from pydantic import BaseModel, PrivateAttr

from codeas.codebase import Codebase
from codedoc.prompts import EXPLAIN_MODULE, SUMMARIZE_MODULE
from codedoc.llm import Llm
from codedoc.utils import read_file

logging.basicConfig(level=logging.DEBUG)

NUM_TOKENS = {
    "short_desc": 40,
    "long_desc": 200,
}

class RepoProcessor(BaseModel):
    llm: Llm = Llm()
    codebase: Codebase = Codebase()
    _repo_map: dict = PrivateAttr({})
    
    def generate_documentation(self):
        asyncio.run(self._generate_documentation())
        
    async def _generate_documentation(self):
        self._repo_map["modules_long_desc"] = await self.run_completions(
            prompts_map=self.prompts_modules_long_desc(),
            max_tokens= int(NUM_TOKENS["long_desc"]*1.2)
        )
        self._repo_map["modules_short_desc"] = await self.run_completions(
            prompts_map=self.prompts_modules_short_desc(),
            max_tokens= int(NUM_TOKENS["short_desc"]*1.2)
        )
        
    async def run_completions(self, prompts_map: dict, **kwargs):
        prompts = list(prompts_map.keys())
        responses = {}
        async for response, prompt in self.llm.run_batch_completions(
            prompts, **kwargs
        ):
            logging.info("Gathering request")
            if len(response.choices) == 1:
                if isinstance(prompt, list):
                    key = prompts_map[prompt[0]["content"]]
                    responses[key] = response.choices[0].message.content
                else:
                    key = prompts_map[prompt]
                    responses[key] = response.choices[0].text
            elif len(response.choices) > 1:
                for choice in response.choices:
                    key = prompts_map[prompt[choice.index]]
                    responses[key] = choice.text
        return responses
    
    def prompts_modules_long_desc(self):
        return {
            EXPLAIN_MODULE.format(
                code=read_file(path), num_tokens=NUM_TOKENS["long_desc"]
            ): path 
            for path in self.codebase.get_modules_paths()
        }
    
    def prompts_modules_short_desc(self):
        return {
            SUMMARIZE_MODULE.format(
                text=self._repo_map["modules_long_desc"][path], 
                num_tokens=NUM_TOKENS["short_desc"]
            ): path
            for path in self.codebase.get_modules_paths()
        }
        
if __name__ == "__main__":
    processor = RepoProcessor(
        codebase={"base_dir": "./src"}, 
        llm={"model": "gpt-3.5-turbo-instruct"})
    processor.generate_documentation()
    processor._repo_map