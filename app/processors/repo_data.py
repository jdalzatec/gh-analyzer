"""Repository data processors for the GitHub repository analyzer."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Generator

from app.models.repo import RepoData


def compute_star_avg() -> Generator[float, int, None]:
    total = 0
    count = 0
    avg = 0.0
    while True:
        value = yield avg
        total += value
        count += 1
        avg = total / count


async def average_processor(repo_data: RepoData) -> None:
    _avg_star_tracker = compute_star_avg()
    next(_avg_star_tracker)

    def _clousure_avg_processor(avg_star_tracker: Generator[float, int, None]) -> None:
        avg = avg_star_tracker.send(repo_data.stargazers_count)
        print(f"Average stars: {avg}")

    return _clousure_avg_processor(_avg_star_tracker)


async def recently_updated_processor(repo_data: RepoData) -> None:
    if (datetime.now(tz=UTC) - repo_data.updated_at).total_seconds() < 86400:
        print(
            f"Recently updated repository: {repo_data.full_name} "
            f"- {repo_data.updated_at}"
        )
