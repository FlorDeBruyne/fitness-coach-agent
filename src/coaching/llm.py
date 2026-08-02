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

__all__ = ['get_coaching_response', 'parse_goal_value', 'main']

async def get_coaching_response(message: str | None, client: AsyncOpenAI, context: Optional[dict] = None):
    with open(file=Path("prompts/fitness_coach_nl.md"), mode="r") as file:
        system_prompt = file.read()

    if context:
        uc = context.get("user_context", {})
        context_str = json.dumps(context, indent=2)
        context_str = context_str.replace("[NAAM]", f'{uc.get("firstname", "")} {uc.get("lastname", "")}'.strip())
        message = f"{context_str}\n{message}"

    response = await client.chat.completions.create(
        model=str(os.getenv("MODEL")),
        messages=[
            {"role":"system", "content": system_prompt},
            {"role": "user", "content": message}
        ]
    )

    return response.choices[0].message.content

async def parse_goal_value(text: str) -> dict:
    with open(file=Path("prompts/goal_value_parser.md"), mode="r") as file:
        system_prompt = file.read()

    openai = AsyncOpenAI(
        api_key=os.getenv("OPENAI_API_KEY"),
        base_url=os.getenv("OPENAI_API_URL")
    )

    response = await openai.chat.completions.create(
        model=str(os.getenv("MODEL")),
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": text}
        ]
    )

    raw = response.choices[0].message.content or ""

    try:
        data = json.loads(raw.strip())
    except json.JSONDecodeError:
        start, end = raw.find("{"), raw.rfind("}")
        if start == -1 or end == -1:
            return {"value": None, "unit": None}
        try:
            data = json.loads(raw[start:end + 1])
        except json.JSONDecodeError:
            return {"value": None, "unit": None}

    value = data.get("value")
    unit = data.get("unit")
    return {
        "value": float(value) if isinstance(value, (int, float)) else None,
        "unit": str(unit).strip() if isinstance(unit, str) and unit.strip() else None
    }

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