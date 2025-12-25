import logging
import asyncio
from typing import List, Optional, Union, Dict
from mem0 import AsyncMemory
from app.utils.retry import network_retry
from app.config.settings import get_settings
from app.services.memory.models import MemoryItem

logger = logging.getLogger(__name__)
settings = get_settings()

class MemoryController:
    def __init__(self, memory: AsyncMemory):
        self.memory = memory

    @network_retry()
    async def get_memory(
        self,
        user_id: str,
        *,
        types: Optional[List[str]] = None,
    ) -> List[MemoryItem]:

        try:
            memories = await asyncio.wait_for(
                self.memory.get_all(user_id=user_id),
                timeout=30,
            )
        except Exception as e:
            logger.error(f"Failed to fetch memory for {user_id}: {e}")
            raise

        items: List[MemoryItem] = []

        for m in memories:
            if not isinstance(m, dict):
                logger.warning(f"Unexpected memory format, coercing: {m}")
                m = {
                    "id": "unknown",
                    "user_id": user_id,
                    "memory": str(m),
                    "metadata": {},
                }

            m.setdefault("id", f"mem_{len(items)}")
            m.setdefault("user_id", user_id)
            m.setdefault("memory", m.pop("content", ""))
            m.setdefault("metadata", {})

            item = MemoryItem(**m)

            if types and item.metadata.get("type") not in types:
                continue

            items.append(item)

        return items

    @network_retry()
    async def add_memory(
        self,
        user_id: str,
        data: Union[str, dict],
        *,
        type: str,
        tags: Optional[List[str]] = None,
    ) -> MemoryItem:

        metadata = {"type": type}
        if tags:
            metadata["tags"] = tags

        try:
            result = await asyncio.wait_for(
                self.memory.add(data, user_id=user_id, metadata=metadata),
                timeout=30,
            )
        except Exception as e:
            logger.error(f"Failed to add memory for {user_id}: {e}")
            raise

        payload = None
        if isinstance(result, list) and result:
            payload = result[0]
        elif isinstance(result, dict):
            payload = result.get("results", [result])[0]

        if isinstance(payload, dict):
            payload.setdefault("id", payload.get("memory_id", "unknown"))
            payload.setdefault("user_id", user_id)
            payload.setdefault("memory", payload.get("content", str(data)))
            payload.setdefault("metadata", metadata)
            return MemoryItem(**payload)

        return MemoryItem(
            id="unknown",
            user_id=user_id,
            memory=str(data),
            metadata=metadata,
        )

    @network_retry()
    async def delete_memory(self, user_id: str, memory_id: str) -> None:
        try:
            await asyncio.wait_for(
                self.memory.delete(memory_id),
                timeout=15,
            )
        except Exception as e:
            logger.error(f"Failed deleting memory {memory_id} for {user_id}: {e}")
            raise

    @network_retry()
    async def clear_memory(
        self,
        user_id: str,
        *,
        types: Optional[List[str]] = None,
    ) -> None:

        try:
            if types:
                items = await self.get_memory(user_id, types=types)
                for item in items:
                    await self.memory.delete(item.id)
            else:
                await asyncio.wait_for(
                    self.memory.delete_all(user_id=user_id),
                    timeout=30,
                )
        except Exception as e:
            logger.error(f"Failed clearing memory for {user_id}: {e}")
            raise

    async def summarize_user_context(self, user_id: str) -> str:
        items = await self.get_memory(user_id)

        if not items:
            return "User has no previous history/context."

        return "User Context:\n" + "\n".join(
            f"- {item.content} (type={item.metadata.get('type','general')})"

            for item in items
        )

    @classmethod
    async def create(cls):
        try:
            if settings.MEM0_API_KEY:
                memory = AsyncMemory(api_key=settings.MEM0_API_KEY)
            else:
                memory = await AsyncMemory.from_config({
                    "vector_store": {
                        "provider": "qdrant",
                        "config": {
                            "collection_name": "memories",
                            "host": "qdrant",
                            "port": 6333,
                            "embedding_model_dims": 1024,
                        }
                    },
                    "llm": {
                        "provider": "groq",
                        "config": {
                            "model": "moonshotai/kimi-k2-instruct",
                            "temperature": 0.2,
                        }
                    },
                    "embedder": {
                        "provider": "ollama",
                        "config": {
                            "model": "mxbai-embed-large",
                            "ollama_base_url": "http://ollama:11434"
                        }
                    }
                })
        except Exception as e:
            logger.warning(f"Mem0 init failed, fallback: {e}")
            memory = AsyncMemory()

        return cls(memory)


if __name__ == "__main__":

    async def test_add():
        memory = await MemoryController.create()
        user_id = "test_user123"
        memory_msg = "saya suka golda coffee"

        try:
            result = await memory.add_memory(user_id=user_id, data=memory_msg, type="general")
            return result
        
        except Exception as e:
            raise ValueError(e)
        

    test_adding = asyncio.run(test_add())
    print(test_adding)