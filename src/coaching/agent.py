import asyncio
from src.health.client import get_morning_context
from src.coaching.llm import main
from src.messaging.bot import send_proactive_message
import logging

logger = logging.getLogger(__name__)

__all__ = ["morning_update"]

async def morning_update():
    context = await get_morning_context()
    llm_response = await main(message="Stuur het ochtend bericht op basis van de health context.",
                              context=context)

    await send_proactive_message(llm_response)


if __name__ == "__main__":
    asyncio.run(morning_update())