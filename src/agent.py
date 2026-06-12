import asyncio
from health_client import get_morning_context, get_evening_context, get_workout_context
from llm_client import main
from telegram_client import send_message
import logging

logger = logging.getLogger(__name__)

async def morning_update():
    context = await get_morning_context()
    llm_response = await main(message="Stuur het ochtend bericht op basis van de health context.",
                              context=context)
    logger.info(llm_response)
    await send_message(llm_response)


if __name__ == "__main__":
    asyncio.run(morning_update())