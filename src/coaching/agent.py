import asyncio
import logging
from src.health.client import HealthClient
from src.coaching.llm import main
from src.messaging.bot import send_proactive_message
from src.users.crud import get_get_all_onboarded_users

logger = logging.getLogger(__name__)

__all__ = ["morning_update"]

async def morning_update():

    for user in await get_get_all_onboarded_users():
        health_client = HealthClient(user.firstname, user.lastname)
        health_context = await health_client.get_morning_context()

        user_context = {
            "firstname": user.firstname or health_client.first_name,
            "lastname": user.lastname or health_client.last_name
        }
        context = {
            "user_context": user_context,
            "health_context": health_context
        }

        llm_response = await main(message="Stuur het ochtend bericht op basis van de user en health context.",
                                  context=context)

        await send_proactive_message(llm_response)


if __name__ == "__main__":
    asyncio.run(morning_update())