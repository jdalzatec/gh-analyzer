"""Main entry point for the GitHub repository analyzer."""

from __future__ import annotations

import asyncio
from asyncio import Queue, Semaphore

from aiohttp import ClientSession

from app.consumers.manager import ConsumerManager
from app.fetchers.github import fetch_repo_data
from app.models.repo import RepoData
from app.processors.repo_data import average_processor, recently_updated_processor


async def main():
    repos = [
        "tiangolo/fastapi",
        "pallets/flask",
        "django/django",
        "jdalzatec/vegas",
    ]
    print("Analyzing repositories...")
    semaphore = Semaphore(5)
    queue = Queue()
    consumer = (
        ConsumerManager[RepoData](queue)
        .add_consumer(average_processor)
        .add_consumer(recently_updated_processor)
    )
    async with consumer:
        async with ClientSession() as session:
            tasks = (fetch_repo_data(session, semaphore, queue, repo) for repo in repos)
            for result in asyncio.as_completed(tasks):
                was_enqueued = await result
                print(was_enqueued)

        await queue.join()
