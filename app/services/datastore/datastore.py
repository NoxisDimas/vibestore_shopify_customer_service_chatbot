import httpx
import logging
import mimetypes
from pathlib import Path
from typing import Optional, Dict, Any, Union
from app.utils.retry import network_retry
from fastapi import UploadFile
from app.config.settings import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

class LightRAGClient:
    def __init__(self, base_url: str = "http://lightrag:9621"):
        self.base_url = base_url.rstrip("/")

    @network_retry()
    async def _request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        url = f"{self.base_url}{endpoint}"
        async with httpx.AsyncClient(timeout=120.0) as client:
            try:
                response = await client.request(method, url, **kwargs)
                response.raise_for_status()
                return response.json()
            except httpx.HTTPStatusError as e:
                logger.error(f"HTTP error requesting {url}: {e.response.text}")
                raise
            except Exception as e:
                logger.error(f"Error communicating with LightRAG: {e}")
                raise

    async def check_health(self) -> bool:
        try:
            # Assuming a health endpoint exists or root returns 200
            await self._request("GET", "/health") 
            return True
        except:
            return False

    async def insert_text(self, text: str, description: Optional[str] = None) -> Dict[str, Any]:
        """Insert raw text into LightRAG."""
        payload = {"text": text}
        if description:
            payload["description"] = description
        return await self._request("POST", "/documents/text", json=payload)

    async def insert_file(self, file: Union[UploadFile, str, Path], domain: Optional[str] = None) -> Dict[str, Any]:
        """
        Insert a file into LightRAG using multipart upload.
        Supports FastAPI UploadFile or a local file path.
        """
        if isinstance(file, (str, Path)):
            path = Path(file)
            if not path.exists():
                raise FileNotFoundError(f"File not found: {path}")
            mime = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
            files = {"file": (path.name, path.open("rb"), mime)}
        else:
            mime = file.content_type or "application/octet-stream"
            files = {"file": (file.filename, file.file, mime)}

        params = {"domain": domain} if domain else None
        return await self._request("POST", "/documents/upload", files=files, params=params)

    async def query(self, query: str, mode: str = "global") -> str:
        """
        Query LightRAG.
        modes: 'global', 'local', 'hybrid', 'naive'
        """
        payload = {
            "query": query,
            "mode": mode
        }
        response = await self._request("POST", "/query", json=payload)
        if isinstance(response, dict) and "response" in response:
            return response["response"]
        return str(response)

lightrag_client = LightRAGClient(base_url=getattr(settings, "LIGHTRAG_API_URL", "http://lightrag:9621")) 