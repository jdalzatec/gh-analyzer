"""Models for the GitHub repository analyzer."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class RepoData(BaseModel):
    full_name: str
    stargazers_count: int
    forks_count: int
    updated_at: datetime
