import logging
import fastapi
from src.coaching.llm import main

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")

app = fastapi.FastAPI()

@app.post("/message/{message}")
async def post_response(message: str):
    return await main(message)
