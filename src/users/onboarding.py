import sqlalchemy
from typing import Optional
import logging
from src.users.models import User
from src.health.client import get_open_wearables_user_id
from src.users.crud import get_record_by_user, get_record_by_id, get_record_by_telegram, add_record

__all__ = ['check_onboarding', 'save_onboarding']

logger = logging.getLogger(__name__)

async def check_onboarding(telegram_chat_id: str | None = None, user_id: str | None = None) -> bool:
    if telegram_chat_id:
        user = await get_record_by_telegram(User, telegram_chat_id)
        return True if user else False
    if user_id:
        user = await get_record_by_user(User, user_id)
        return True if user else False
    return False

async def save_onboarding(data: dict) -> bool:
    try:
        logger.info(f"Saving onboarding data: {data}")
        open_wearables_user = await get_open_wearables_user_id(data.get('firstname'), data.get('lastname'))
        logger.info(f"Got the open wearable user: {open_wearables_user}")
        data.update({
            'open_wearables_user_id': open_wearables_user.get("id", "") if open_wearables_user else None, #removed the get to see what the actual return is
        })

        status = await add_record(User, data)
        return True if status else False
    except Exception as e:
        logger.error(f"Error saving onboarding data: {e}, {data}")
        return False
