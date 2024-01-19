import asyncio
from pydantic import BaseModel, PrivateAttr

from codeas.codebase import Codebase
from codedoc.prompts import EXPLAIN, EXPLAIN_MODULE
from codedoc.llm import Llm
from codedoc.utils import read_file

class RepoProcessor(BaseModel):
    llm: Llm = Llm()
    codebase: Codebase = Codebase()
    _repo_map: dict = PrivateAttr({})
    
    def generate_documentation(self):
        self._repo_map["modules_desc"] = asyncio.run(
            self.generate_modules_doc(
                EXPLAIN_MODULE,
                num_tokens=200,
                openai_args={"max_tokens": 220})
        )
        
    async def generate_modules_doc(self, template: str, openai_args: dict, **template_args):
        modules_doc = {}
        prompts = self.get_module_prompts(template, **template_args)
        mapping = self.get_prompt_mapping(prompts)
        async for response, prompt in self.llm.run_batch_completions(
            prompts, **openai_args
        ):
            if len(response.choices) == 1:
                if isinstance(prompt, list):
                    module = mapping[prompt[0]["content"]]
                    modules_doc[module] = response.choices[0].message.content
                else:
                    module = mapping[prompt]
                    modules_doc[module] = response.choices[0].text
            elif len(response.choices) > 1:
                for choice in response.choices:
                    module = mapping[prompt[choice.index]]
                    modules_doc[module] = choice.text
        return modules_doc
    
    def get_module_prompts(self, template, **kwargs):
        return [
            template.format(code=read_file(path), **kwargs) 
            for path in self.codebase.get_modules_paths()
        ]
    
    def get_prompt_mapping(self, prompts):
        return dict(zip(prompts, self.codebase.get_modules_paths()))
        
if __name__ == "__main__":
    processor = RepoProcessor(
        codebase={"base_dir": "./src"}, 
        llm={"model": "gpt-3.5-turbo-1106"})
    processor.generate_documentation()
    processor._repo_map