import os
import json
import yaml
import logging
import asyncio
from typing import Optional
from pathlib import Path
from dotenv import load_dotenv
from openai import AsyncOpenAI
from datetime import datetime, timedelta

load_dotenv()

async def get_coaching_response(message: str | None, client: AsyncOpenAI, context: Optional[dict] = None):

    with open(file=Path("prompts/fitness_coach_nl.md"), mode="r") as file:
        system_prompt = file.read()

    if context:
        context_str = json.dumps(context, indent=2)
        message = f"{context_str}\n{message}"

    response = await client.chat.completions.create(
        model=os.getenv("MODEL"),
        messages=[{"role":"system", "content": system_prompt},
                  {"role": "user", "content": message}]
    )

    return response.choices[0].message.content

async def main (message: str | None, context: Optional[dict] = None):
    openai = AsyncOpenAI(
        api_key=os.getenv("OPENAI_API_KEY"),
        base_url=os.getenv("OPENAI_API_URL")
    )

    result = await get_coaching_response(message=message,
                                         client=openai,
                                         context=context)
    return result

if __name__ == "__main__":
    asyncio.run(main("Hello brev"))