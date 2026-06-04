import os
import asyncio
from dotenv import load_dotenv
from openai import AsyncOpenAI

load_dotenv()

async def get_coaching_response(message: str, client: AsyncOpenAI):
    response = await client.chat.completions.create(
        model=os.getenv("MODEL"),
        messages=[{"role":"system", "content":"Je bent een fitness coach. Ik heb 5 uur geslapen en mijn HRV is laag. Wat raad je aan?"},
                  {"role": "user", "content": message}]
    )
    return response.choices[0].message.content

async def main (message: str):
    openai = AsyncOpenAI(
        api_key=os.getenv("OPENAI_API_KEY"),
        base_url=os.getenv("OPENAI_API_URL")
    )

    result = await get_coaching_response(message=message, client=openai)
    return result

if __name__ == "__main__":
    asyncio.run(main("Test brev"))