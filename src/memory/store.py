import os
import uuid
import logging
from datetime import datetime, timezone
from dotenv import load_dotenv
from openai import AsyncOpenAI
from qdrant_client import AsyncQdrantClient
from qdrant_client.models import PointStruct, VectorParams, Distance, Filter, FieldCondition, MatchValue

load_dotenv()
logger = logging.getLogger(__name__)

COLLECTION_NAME = "memories"
VECTOR_SIZE = 768
EMBEDDING_MODEL = "nomic-embed-text"

MEMORY_CATEGORIES = ['voorkeur', 'routine', 'levensgebeurtenis', 'gemoedstoestand', 'feedback_op_coach']

__all__ = ['MEMORY_CATEGORIES', 'ensure_collection', 'save_memory', 'search_memory']

def _qdrant_client() -> AsyncQdrantClient:
    return AsyncQdrantClient(
        url=os.getenv("QDRANT_URL"),
        api_key=os.getenv("QDRANT_API_KEY")
    )

def _openai_client() -> AsyncOpenAI:
    return AsyncOpenAI(
        api_key=os.getenv("OPENAI_API_KEY"),
        base_url=os.getenv("OPENAI_API_URL")
    )

async def _embed(text: str) -> list[float]:
    client = _openai_client()
    response = await client.embeddings.create(model=EMBEDDING_MODEL, input=text)
    return response.data[0].embedding

async def ensure_collection() -> None:
    client = _qdrant_client()
    if not await client.collection_exists(COLLECTION_NAME):
        await client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=VectorParams(size=VECTOR_SIZE, distance=Distance.COSINE)
        )
        logger.info(f"Created Qdrant collection '{COLLECTION_NAME}'")

async def save_memory(user_id: str, text: str, category: str) -> bool:
    try:
        await ensure_collection()
        vector = await _embed(text)

        client = _qdrant_client()
        await client.upsert(
            collection_name=COLLECTION_NAME,
            points=[
                PointStruct(
                    id=str(uuid.uuid4()),
                    vector=vector,
                    payload={
                        "text": text,
                        "category": category,
                        "user_id": user_id,
                        "created_at": datetime.now(timezone.utc).isoformat(),
                    }
                )
            ]
        )
        logger.info(f"Saved memory for user {user_id}: {text}")
        return True
    except Exception as e:
        logger.error(f"Error saving memory: {e}")
        return False

async def search_memory(user_id: str, query: str, top_k: int = 3) -> list[dict]:
    vector = await _embed(query)
    client = _qdrant_client()

    result = await client.query_points(
        collection_name=COLLECTION_NAME,
        query=vector,
        query_filter=Filter(must=[FieldCondition(key="user_id", match=MatchValue(value=user_id))]),
        limit=top_k
    )
    return [point.payload for point in result.points]
