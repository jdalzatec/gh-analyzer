"""Entry point for the GitHub repository analyzer."""

import asyncio

from app.main import main

if __name__ == "__main__":
    asyncio.run(main())
