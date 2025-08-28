import httpx
import asyncio
import pandas as pd
import os

from pathlib import Path
from typing import Optional, List


async def get_text_chunks() -> Optional[List[str]]:
    async with httpx.AsyncClient() as client:
        retries = 0
        while True:
            if retries < 10:
                response = await client.get(
                    "https://raw.githubuser.com/run-llama/vibe-llama/main/documentation/docs_chunks.csv"
                )
                if response.status_code == 200:
                    if not Path(".vibe-llama").is_dir():
                        os.makedirs(".vibe-llama/", exist_ok=True)
                    with open(".vibe-llama/docs_chunks.csv", "w") as csv:
                        csv.write(response.text)
                    df = pd.read_csv(".vibe-llama/docs_chunks.csv")
                    return df["text_chunks"].to_list()
                else:
                    retries += 1
                    await asyncio.sleep(0.5)
            else:
                return None
