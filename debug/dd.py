import asyncio

async def print_numbers():
    for i in range(5):
        print(f"Number: {i}")
        await asyncio.sleep(1)

async def print_letters():
    for letter in "ABCDE":
        print(f"Letter: {letter}")
        await asyncio.sleep(1)

async def main():
    task1 = asyncio.create_task(print_numbers())
    task2 = asyncio.create_task(print_letters())

    await asyncio.gather(task1, task2)

asyncio.run(main())
