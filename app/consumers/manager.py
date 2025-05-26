"""Consumers for the GitHub repository analyzer."""

from __future__ import annotations

import asyncio
from asyncio import Queue
from typing import Awaitable, Callable, Generic, List, TypeVar

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
