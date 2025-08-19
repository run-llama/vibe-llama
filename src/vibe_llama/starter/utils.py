import os
import httpx
import asyncio

from pathlib import Path
from typing import Optional


def write_file(file_path: str, content: str, service_url: str) -> None:
    directory = os.path.dirname(file_path)
    if not Path(directory).is_dir():
        os.makedirs(directory, exist_ok=True)
    if Path(file_path).is_file():
        with open(file_path) as f:
            file_content = f.read()
        content = file_content + "\n" + content
    if file_path.startswith(".cursor"):
        frontmatter = f"""---
description: Instructions from {service_url} for Cursor coding agent
alwaysApply: false
---

"""
        content = frontmatter + "\n" + content
    with open(file_path, "w") as w:
        w.write(content)
    return None


async def get_instructions(
    instructions_url: str, max_retries: int = 10, retry_interval: float = 0.5
) -> Optional[str]:
    async with httpx.AsyncClient() as client:
        retries = 0
        while True:
            if retries < max_retries:
                response = await client.get(instructions_url)
                if response.status_code == 200:
                    return response.text
                else:
                    retries += 1
                    await asyncio.sleep(retry_interval)
            else:
                return None
