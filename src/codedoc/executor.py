import asyncio


class AsyncExecutor:
    def __init__(self, func):
        self.func = func
        self.loop = asyncio.new_event_loop()

    def __call__(self, *args, **kwargs):
        try:
            if asyncio.iscoroutinefunction(self.func):
                # The function is a coroutine
                coro = self.func(*args, **kwargs)
                return self.loop.run_until_complete(coro)
            else:
                # The function is a regular function
                future = self.loop.run_in_executor(None, self.func, *args, **kwargs)
                return self.loop.run_until_complete(future)
        finally:
            self.loop.close()

    def __del__(self):
        if not self.loop.is_closed():
            self.loop.close()
