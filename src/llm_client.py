import os
import yaml
import logging
import asyncio
from pathlib import Path
from dotenv import load_dotenv
from openai import AsyncOpenAI
from datetime import datetime, timedelta

load_dotenv()

async def get_coaching_response(message: str, client: AsyncOpenAI):

    with open(file=Path("prompts/fitness_coach_nl.md"), mode="r") as file:
        system_prompt = file.read()

    response = await client.chat.completions.create(
        model=os.getenv("MODEL"),
        messages=[{"role":"system", "content": system_prompt},
                  {"role": "user", "content": message}]
    )

    return response.choices[0].message.content

async def main (message: str):
    openai = AsyncOpenAI(
        api_key=os.getenv("OPENAI_API_KEY"),
        base_url=os.getenv("OPENAI_API_URL")
    )

    result = await get_coaching_response(message=message, client=openai)
    return result

if __name__ == "__main__":
    asyncio.run(main("Hello brev"))