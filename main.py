from __future__ import annotations

import asyncio
from asyncio import Queue, Semaphore
from datetime import datetime
from typing import Awaitable, Callable, Generic, List, TypeVar

from aiohttp import ClientSession
from pydantic import BaseModel


class RepoData(BaseModel):
    full_name: str
    stargazers_count: int
    forks_count: int
    updated_at: datetime


async def fetch_repo_data(
    session: ClientSession, semaphore: Semaphore, queue: Queue, repo_name: str
) -> bool:
    async with semaphore:
        print(f"Fetching data for {repo_name}...")
        url = f"https://api.github.com/repos/{repo_name}"
        headers = {
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }
        if repo_name == "tiangolo/fastapi":
            await asyncio.sleep(10)

        async with session.get(url, headers=headers) as response:
            if response.status == 200:
                data = await response.json()
                repo_data = RepoData(
                    full_name=data["full_name"],
                    stargazers_count=data["stargazers_count"],
                    forks_count=data["forks_count"],
                    updated_at=data["updated_at"],
                )
                await queue.put(repo_data)
                return True
            else:
                print(f"Failed to fetch data for {repo_name}: {response.status}")
                return False


T = TypeVar("T")
Consumer = Callable[[T], Awaitable[None]]


class ConsumerManager(Generic[T]):

    def __init__(self, queue: Queue):
        self.queue = queue
        self.task = asyncio.create_task(self._consume())
        self._consumers: List[Consumer] = []

    def add_consumer(self, consumer_func: Consumer) -> ConsumerManager:
        self._consumers.append(consumer_func)
        return self

    async def _consume(self) -> None:
        try:
            while True:
                item = await self.queue.get()
                if item is None:
                    print("Consumer shutting down...")
                    break

                await asyncio.gather(
                    *(consumer(item) for consumer in self._consumers),
                    return_exceptions=True,
                )

                self.queue.task_done()
        except asyncio.CancelledError:
            print("Consumer task was cancelled.")

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        await self.queue.put(None)
        await self.task


async def my_method(repo_data: RepoData) -> None:
    print(f"Processing {repo_data}")


async def main():
    repos = [
        "tiangolo/fastapi",
        "django/django",
        "pallets/flask",
    ]
    print("Analyzing repositories...")
    semaphore = Semaphore(5)
    queue = Queue()
    consumer = ConsumerManager[RepoData](queue).add_consumer(my_method)
    async with consumer:
        async with ClientSession() as session:
            tasks = (fetch_repo_data(session, semaphore, queue, repo) for repo in repos)
            for result in asyncio.as_completed(tasks):
                was_enqueued = await result
                print(was_enqueued)

        await queue.join()


asyncio.run(main())
