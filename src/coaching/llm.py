import os
import json
import logging
import asyncio
from typing import Optional
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv
from openai import AsyncOpenAI

from src.users.models import User
from src.users.goals import get_active_goals, serialize_goal
from src.users.injuries import get_active_injuries, serialize_injury
from src.memory.store import search_memory

load_dotenv()
logger = logging.getLogger(__name__)

__all__ = ['get_coaching_response', 'main']

FITNESS_LEVEL_MAP = {
    "inactive": "inactief",
    "lightly active": "licht actief",
    "moderately active": "matig actief",
    "very active": "erg actief",
    "athlete": "atleet",
}

def _normalize_fitness_level(level: Optional[str]) -> Optional[str]:
    if not level:
        return None
    return FITNESS_LEVEL_MAP.get(level.strip().lower(), level)

async def _build_context(user: Optional[User], health_context: Optional[dict], message: Optional[str]) -> dict:
    context = {"date": datetime.now().date().isoformat()}

    if health_context:
        context["health_context"] = health_context

    if user:
        context["user_name"] = f"{user.firstname} {user.lastname}".strip()
        context["fitness_level"] = _normalize_fitness_level(user.fitness_level)
        active_goals = await get_active_goals(user.id)
        context["goals"] = [serialize_goal(goal) for goal in active_goals]
        active_injuries = await get_active_injuries(user.id)
        context["injuries"] = [serialize_injury(injury) for injury in active_injuries]
        if message:
            memories = await search_memory(user_id=str(user.id), query=message, top_k=3)
            context["memories"] = [{"category": m["category"], "text": m["text"]} for m in memories]

    return context

async def get_coaching_response(
    message: str | None,
    client: AsyncOpenAI,
    user: Optional[User] = None,
    health_context: Optional[dict] = None
):
    with open(file=Path("prompts/fitness_coach_nl.md"), mode="r") as file:
        system_prompt = file.read()

    context = await _build_context(user, health_context, message)
    if context:
        context_str = json.dumps(context, indent=2)
        message = f"{context_str}\n{message}"

    response = await client.chat.completions.create(
        model=str(os.getenv("MODEL")),
        temperature=0.4,
        messages=[
            {"role":"system", "content": system_prompt},
            {"role": "user", "content": message}
        ]
    )

    return response.choices[0].message.content

async def main(message: str | None, user: Optional[User] = None, health_context: Optional[dict] = None):
    openai = AsyncOpenAI(
        api_key=os.getenv("OPENAI_API_KEY"),
        base_url=os.getenv("OPENAI_API_URL")
    )

    result = await get_coaching_response(message=message,
                                         client=openai,
                                         user=user,
                                         health_context=health_context)
    return result

if __name__ == "__main__":
    asyncio.run(main("Hello brev"))
