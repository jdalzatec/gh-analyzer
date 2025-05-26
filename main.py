from __future__ import annotations

import asyncio
from asyncio import Queue, Semaphore
from datetime import UTC, datetime
from typing import Awaitable, Callable, Generator, Generic, List, TypeVar

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
            await asyncio.sleep(1)

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

                results = await asyncio.gather(
                    *(consumer(item) for consumer in self._consumers),
                    return_exceptions=True,
                )
                for result in results:
                    if isinstance(result, Exception):
                        print(f"Consumer raised an exception: {result}")

                self.queue.task_done()
        except asyncio.CancelledError:
            print("Consumer task was cancelled.")

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        await self.queue.put(None)
        await self.task


async def average_processor(
    avg_star_tracker: Generator[float, int, None], repo_data: RepoData
) -> None:
    avg = avg_star_tracker.send(repo_data.stargazers_count)
    print(f"Average stars: {avg}")


async def recently_updated_processor(repo_data: RepoData) -> None:
    if (datetime.now(tz=UTC) - repo_data.updated_at).total_seconds() < 86400:
        print(
            f"Recently updated repository: {repo_data.full_name} - {repo_data.updated_at}"
        )


def compute_star_avg() -> Generator[float, int, None]:
    total = 0
    count = 0
    avg = 0.0
    while True:
        print("Computing average stars...")
        value = yield avg
        total += value
        count += 1
        avg = total / count


async def main():
    repos = [
        "tiangolo/fastapi",
        "pallets/flask",
        "django/django",
    ]
    print("Analyzing repositories...")
    semaphore = Semaphore(5)
    queue = Queue()
    avg_star_tracker = compute_star_avg()
    next(avg_star_tracker)
    consumer = (
        ConsumerManager[RepoData](queue)
        .add_consumer(lambda rd: average_processor(avg_star_tracker, rd))
        .add_consumer(recently_updated_processor)
    )
    async with consumer:
        async with ClientSession() as session:
            tasks = (fetch_repo_data(session, semaphore, queue, repo) for repo in repos)
            for result in asyncio.as_completed(tasks):
                was_enqueued = await result
                print(was_enqueued)

        await queue.join()


asyncio.run(main())
