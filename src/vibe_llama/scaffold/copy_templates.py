import httpx
from collections import defaultdict
import asyncio
from typing import Optional, Dict

from vibe_llama.constants import BASE_URL

base_url = f"{BASE_URL}/templates/"
files = ["workflow.py", "README.md"]


async def get_template_files(
    template_name: str, max_retries: int = 10, retry_interval: float = 0.5
) -> Optional[Dict[str, str]]:
    contents = defaultdict(str)
    for file in files:
        async with httpx.AsyncClient() as client:
            retries = 0
            while True:
                if retries < max_retries:
                    response = await client.get(base_url + template_name + "/" + file)
                    if response.status_code == 200:
                        contents[file] = response.text
                        break
                    else:
                        retries += 1
                        await asyncio.sleep(retry_interval)
                else:
                    break
    if not contents[files[0]] and not contents[files[1]]:
        return None
    else:
        return dict(contents)
