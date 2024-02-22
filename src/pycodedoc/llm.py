import asyncio
import logging
from typing import ClassVar

from openai import AsyncOpenAI, OpenAI
from pydantic import BaseModel, PrivateAttr
from tenacity import retry, stop_after_attempt
from tqdm.asyncio import tqdm_asyncio


def log_retry(retry_state):
    logging.info(
        "Retrying %s: attempt #%s ended with: %s",
        retry_state.fn,
        retry_state.attempt_number,
        retry_state.outcome,
    )


class Llm(BaseModel):
    batch_size: int = 100
    max_retries: int = 5
    _client: ClassVar[OpenAI] = PrivateAttr(OpenAI())

    def run_completions(self, messages, model="gpt-3.5-turbo-1106", **kwargs) -> list:
        """runs completions synchronously"""
        response = self._client.chat.completions.create(
            messages=messages, model=model, **kwargs
        )
        if "stream" in kwargs and kwargs["stream"]:
            response = self._parse_stream(response)
        return response

    def _parse_stream(self, stream):
        """parses stream response from completions"""
        response = {"role": "assistant", "content": None, "tool_calls": None}
        for chunk in stream:
            choice = chunk.choices[0]
            if choice.delta and choice.delta.content:
                self._parse_delta_content(choice.delta, response)
            elif choice.delta and choice.delta.tool_calls:
                self._parse_delta_tools(choice.delta, response)
        return response

    def run_batch_completions(self, messages_batches: list, **kwargs) -> list:
        """run completions by batch asynchronously"""
        return asyncio.run(self._run_batch_completions(messages_batches, **kwargs))

    async def _run_batch_completions(self, messages_batches: list, **kwargs) -> list:
        """runs completions by batch asynchronously"""
        async with AsyncOpenAI(max_retries=self.max_retries) as client:
            coroutines = [
                self._run_async_completions(client, messages, **kwargs)
                for messages in messages_batches
            ]
            responses = []
            async for batch_responses in self._run_batches(coroutines):
                responses.extend(batch_responses)
            return responses

    @retry(stop=stop_after_attempt(3), after=log_retry)
    async def _run_async_completions(
        self, client, messages, model="gpt-3.5-turbo-1106", **kwargs
    ):
        """runs completions asynchronously"""
        response = await client.chat.completions.create(
            messages=messages, model=model, **kwargs
        )
        if "stream" in kwargs and kwargs["stream"]:
            response = await self._parse_async_stream(response)
        return response

    async def _parse_async_stream(self, stream):
        """parses stream response from async completions"""
        response = {"role": "assistant", "content": None, "tool_calls": None}
        async for chunk in stream:
            choice = chunk.choices[0]
            if choice.delta and choice.delta.content:
                self._parse_delta_content(choice.delta, response)
            elif choice.delta and choice.delta.tool_calls:
                self._parse_delta_tools(choice.delta, response)
        return response

    async def _run_batches(self, coroutines: list):
        for batch in self._batches(coroutines, self.batch_size):
            yield await tqdm_asyncio.gather(*batch)

    def _batches(self, items, batch_size):
        for i in range(0, len(items), batch_size):
            yield items[i : i + batch_size]

    def _parse_delta_content(self, delta, response):
        if response["content"] is None:
            response["content"] = ""

        response["content"] += delta.content

    def _parse_delta_tools(self, delta, response):
        if response["tool_calls"] is None:
            response["tool_calls"] = []

        for tchunk in delta.tool_calls:
            if len(response["tool_calls"]) <= tchunk.index:
                response["tool_calls"].append(
                    {
                        "id": "",
                        "type": "function",
                        "function": {"name": "", "arguments": ""},
                    }
                )
            if tchunk.id:
                response["tool_calls"][tchunk.index]["id"] += tchunk.id
            if tchunk.function.name:
                response["tool_calls"][tchunk.index]["function"][
                    "name"
                ] += tchunk.function.name
            if tchunk.function.arguments:
                response["tool_calls"][tchunk.index]["function"][
                    "arguments"
                ] += tchunk.function.arguments
