import fastapi
from src.coaching.llm import main

app = fastapi.FastAPI()

@app.post("/message/{message}")
async def post_response(message: str):
    return await main(message)
