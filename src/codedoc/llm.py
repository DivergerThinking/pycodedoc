import asyncio

from openai import (
    APITimeoutError,
    AsyncOpenAI,
    InternalServerError,
    RateLimitError,
    UnprocessableEntityError,
)
from pydantic import BaseModel
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)


class Llm(BaseModel):
    model: str = "gpt-3.5-turbo-1106"
    batch_size: int = 50

    async def run_completions(self, prompts: list, **kwargs) -> list:
        responses_map = []
        async for response, prompt in self._run_batch_completions(prompts, **kwargs):
            responses_map.append((response, prompt))
        self._sort_responses(prompts, responses_map)
        responses = [response for response, _ in responses_map]
        return responses

    async def _run_batch_completions(self, prompts: list, **kwargs):
        async with AsyncOpenAI() as client:
            calls = [
                self._run_chat_completions(client, prompt, **kwargs)
                for prompt in prompts
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
                UnprocessableEntityError,
            )
        ),
    )
    async def _run_chat_completions(self, client, prompt, **kwargs):
        messages = [{"role": "user", "content": prompt}]
        return (
            await client.chat.completions.create(
                model=self.model, messages=messages, **kwargs
            ),
            prompt,
        )

    def _batches(self, prompts, batch_size):
        for i in range(0, len(prompts), batch_size):
            yield prompts[i : i + batch_size]

    def _sort_responses(self, prompts, responses):
        responses.sort(key=lambda x: prompts.index(x[1]))


# if __name__ == "__main__":
#     async def run():
#         prompts = ["hello world"] * 10
#         llm = Llm()#model="gpt-3.5-turbo-1106")
#         async for response, prompt in llm.run_batch_completions(prompts):
#             print("RESULT",response.usage)

#     asyncio.run(run())
