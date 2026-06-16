import sqlalchemy
from typing import Optional
__all__ = ['check_onboarding']

async def check_onboarding(telegram_chat_id: Optional[str | None], user_id: Optional[str | None]) -> bool:

    return False