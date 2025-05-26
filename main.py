import asyncio
from asyncio import Semaphore, Queue
from aiohttp import ClientSession
from datetime import datetime
from pydantic import BaseModel

class RepoData(BaseModel):
    full_name: str
    stargazers_count: int
    forks_count: int
    updated_at: datetime

async def fetch_repo_data(session: ClientSession, semaphore: Semaphore, queue: Queue, repo_name: str) -> RepoData:
    async with semaphore:
        print(f"Fetching data for {repo_name}...")
        url = f"https://api.github.com/repos/{repo_name}"
        headers = {
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28"
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
                    updated_at=data["updated_at"]
                )
                await queue.put(repo_data)
            else:
                print(f"Failed to fetch data for {repo_name}: {response.status}")
                return None



async def main():
    repos = [
        "tiangolo/fastapi",
        "django/django",
        "pallets/flask",
    ]
    print('Analyzing repositories...')
    semaphore = Semaphore(1)
    queue = Queue()
    async with ClientSession() as session:
        tasks = (fetch_repo_data(session, semaphore, queue, repo) for repo in repos)
        for result in asyncio.as_completed(tasks):
            repo_data = await result
            print(queue.qsize())

asyncio.run(main())