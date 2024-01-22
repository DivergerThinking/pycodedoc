from pydantic import BaseModel
import asyncio
from openai import AsyncOpenAI
from openai import APITimeoutError, InternalServerError, RateLimitError, UnprocessableEntityError
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

class Llm(BaseModel):
    model: str = "gpt-3.5-turbo-instruct"
    batch_size: int = 10
    
    async def run_batch_completions(self, prompts, **kwargs):
        async with AsyncOpenAI() as client:
            # legacy api can take batches of 20 prompts at once
            prebatched_prompts = (
                self._batches(prompts, 20) if self.model == "gpt-3.5-turbo-instruct" 
                else prompts
            )
            calls = [
                self._run_completions(client, prompt, **kwargs) 
                for prompt in prebatched_prompts
            ]
            for batch in self._batches(calls, self.batch_size):
                for future in asyncio.as_completed(batch):
                    yield await future
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(min=2, max=5),
        retry=retry_if_exception_type(
            (
                APITimeoutError,
                InternalServerError,
                RateLimitError,
                UnprocessableEntityError
            )
        )
    )
    async def _run_completions(self, client, prompt, **kwargs):
        if self.model == "gpt-3.5-turbo-instruct":
            return await self._run_legacy_completions(client, prompt, **kwargs)
        else:
            return await self._run_chat_completions(client, prompt, **kwargs)
    
    async def _run_legacy_completions(self, client, prompt, **kwargs):
        return await client.completions.create(
            model="gpt-3.5-turbo-instruct",
            prompt=prompt,
            **kwargs,
        ), prompt
        
    async def _run_chat_completions(self, client, prompt, **kwargs):
        messages = [{"role": "user", "content": prompt}]
        return await client.chat.completions.create(
            model=self.model,
            messages=messages,
            **kwargs
        ), messages
    
    def _batches(self, prompts, batch_size):
        for i in range(0, len(prompts), batch_size):
            yield prompts[i : i + batch_size]
            
if __name__ == "__main__":
    async def run():        
        prompts = ["hello world"] * 10
        llm = Llm()#model="gpt-3.5-turbo-1106")
        async for response, prompt in llm.run_batch_completions(prompts):
            print("RESULT",response.usage)
    
    asyncio.run(run())
