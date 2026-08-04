import sys
import asyncio
import logging
from src.health.client import HealthClient, get_open_wearables_user_id
from src.coaching.llm import main
from src.messaging.bot import send_proactive_message
from src.users.crud import get_get_all_onboarded_users
from src.users.models import User

logger = logging.getLogger(__name__)

__all__ = ["morning_update"]

async def morning_update():

    for user in await get_get_all_onboarded_users():
        open_wearables_id = user.open_wearables_user_id if user.open_wearables_user_id else await get_open_wearables_user_id(user.firstname, user.lastname)
        health_client = HealthClient(open_wearables_id)
        health_context = await health_client.get_morning_context()

        llm_response = await main(message="Stuur het ochtend bericht op basis van de user en health context.",
                                  user=user,
                                  health_context=health_context)

        await send_proactive_message(llm_response)


async def evening_update():

    for user in await get_get_all_onboarded_users():
        health_client = HealthClient(user.open_wearables_user_id)
        health_context = await health_client.get_evening_context()

        llm_response = await main(message="Stuur het avond bericht op basis van de user en health context.",
                                  user=user,
                                  health_context=health_context)

        await send_proactive_message(llm_response)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    if len(sys.argv) > 1 and sys.argv[1] == "evening":
        asyncio.run(evening_update())
    else:
        asyncio.run(morning_update())
