import sqlalchemy
from typing import Optional
from src.users.models import User
from src.users.crud import get_record_by_user, get_record_by_id, get_record_by_telegram, add_record
__all__ = ['check_onboarding', 'save_onboarding']

async def check_onboarding(telegram_chat_id: str | None = None, user_id: str | None = None) -> bool:
    if telegram_chat_id:
        user = await get_record_by_telegram(User, telegram_chat_id)
        return True if user else False
    if user_id:
        user = await get_record_by_user(User, user_id)
        return True if user else False
    return False

async def save_onboarding(data: dict) -> bool:
    status = await add_record(User, data)
    return True if status else False