import asyncio
import logging
from pydantic import BaseModel, PrivateAttr

from codeas.codebase import Codebase
from codedoc.llm import Llm
from codedoc.prompts import modules_desc_args, project_desc_args

logging.basicConfig(level=logging.INFO)


class RepoProcessor(BaseModel):
    llm: Llm = Llm(model="gpt-3.5-turbo-1106")
    codebase: Codebase = Codebase()
    _docu: dict = PrivateAttr({})
    
    def generate_documentation(self):
        asyncio.run(self._generate_documentation())
        self.write_markdown()
    
    def write_markdown(self):
        md = "# Project Overview\n"
        md += f"{self._docu['project_desc']}\n\n"
        
        md += "## Folder structure\n"
        md += f"{self.codebase.get_tree()}\n\n"
        
        md += "## Modules\n"
        for name, desc in self._docu["modules_desc"].items():
            md += f"### {name}\n"
            md += f"{desc}\n\n"

        with open("modules-instruct.md", "w") as f:
            f.write(md)
        
    async def _generate_documentation(self):
        self._docu[f"modules_desc"] = await self.run_completions(**modules_desc_args(self))
        self._docu[f"project_desc"] = await self.run_completions(**project_desc_args(self))
        
    async def run_completions(self, prompts_map: dict, **kwargs):
        prompts = list(prompts_map.keys())
        responses = {}
        async for response, prompt in self.llm.run_batch_completions(
            prompts, **kwargs
        ):
            # logging.info("Gathering request")
            if len(response.choices) == 1:
                if hasattr(response.choices[0], "message"):
                    key = prompts_map[prompt[0]["content"]]
                    responses[key] = response.choices[0].message.content
                else:
                    key = (
                        prompts_map[prompt] if isinstance(prompt, str) 
                        else prompts_map[prompt[0]]
                    )
                    responses[key] = response.choices[0].text
            elif len(response.choices) > 1:
                for choice in response.choices:
                    key = prompts_map[prompt[choice.index]]
                    responses[key] = choice.text
        return responses
        
if __name__ == "__main__":
    processor = RepoProcessor(
        codebase={"base_dir": "./src"}, 
        llm={"model": "gpt-3.5-turbo-1106"})
    processor.generate_documentation()
    processor._docu