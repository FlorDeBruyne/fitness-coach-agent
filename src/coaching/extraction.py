import os
import json
import logging
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv
from openai import AsyncOpenAI

from src.users.goals import GOAL_TYPES

load_dotenv()
logger = logging.getLogger(__name__)

__all__ = ['get_structured_response', 'parse_goal_value', 'parse_goal_intro']

async def get_structured_response(prompt_path: str, message: str) -> dict:
    with open(file=Path(prompt_path), mode="r") as file:
        system_prompt = file.read()

    openai = AsyncOpenAI(
        api_key=os.getenv("OPENAI_API_KEY"),
        base_url=os.getenv("OPENAI_API_URL")
    )

    response = await openai.chat.completions.create(
        model=str(os.getenv("MODEL")),
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": message}
        ]
    )

    raw = response.choices[0].message.content or ""

    try:
        return json.loads(raw.strip())
    except json.JSONDecodeError:
        start, end = raw.find("{"), raw.rfind("}")
        if start == -1 or end == -1:
            logger.warning(f"Could not find JSON in LLM response: {raw!r}")
            return {}
        try:
            return json.loads(raw[start:end + 1])
        except json.JSONDecodeError:
            logger.warning(f"Could not parse JSON from LLM response: {raw!r}")
            return {}

async def parse_goal_value(text: str) -> dict:
    data = await get_structured_response("prompts/goal_value_parser.md", text)

    value = data.get("value")
    unit = data.get("unit")
    return {
        "value": float(value) if isinstance(value, (int, float)) else None,
        "unit": str(unit).strip() if isinstance(unit, str) and unit.strip() else None
    }

async def parse_goal_intro(text: str) -> dict:
    today = datetime.now().date().isoformat()
    message = f"Vandaag is {today}.\n{text}"
    data = await get_structured_response("prompts/goal_intro_parser.md", message)

    goal_type = data.get("type")
    deadline = data.get("deadline")

    value = data.get("target_value")
    unit = data.get("unit")
    value = float(value) if isinstance(value, (int, float)) else None
    unit = str(unit).strip() if isinstance(unit, str) and unit.strip() else None
    if value is None or unit is None:
        value, unit = None, None

    return {
        "type": goal_type if goal_type in GOAL_TYPES else None,
        "deadline": deadline if isinstance(deadline, str) else None,
        "target_value": value,
        "unit": unit
    }
