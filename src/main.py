import fastapi
from src.llm_client import main

app = fastapi.FastAPI()

@app.post("/message/{message}")
async def post_response(message: str):
    return await main(message)
