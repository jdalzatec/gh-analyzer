"""Fetchers for the GitHub repository analyzer."""

from __future__ import annotations

import asyncio
from asyncio import Queue, Semaphore

from aiohttp import ClientSession

from app.models.repo import RepoData


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
