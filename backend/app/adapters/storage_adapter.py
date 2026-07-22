"""
Supabase Storage adapter — handles uploading and URL-generating for files.

Uses Supabase's REST Storage API directly via httpx.
No Supabase Python SDK is used — the SDK pulls in several heavyweight
dependencies that would push us toward the Render RAM limit.

The adapter exposes:
  upload_file(path, data, content_type) -> storage_path
  get_signed_url(storage_path, expires_in_seconds) -> url
  delete_file(storage_path) -> None
"""

import logging
import httpx

from app.config import settings

logger = logging.getLogger(__name__)


class SupabaseStorageAdapter:
    def __init__(self):
        self._base_url = f"{settings.supabase_url}/storage/v1"
        self._bucket = settings.supabase_bucket
        self._headers = {
            "Authorization": f"Bearer {settings.supabase_service_key}",
            "apikey": settings.supabase_service_key,
        }

    async def upload_file(
        self,
        path: str,
        data: bytes,
        content_type: str = "application/octet-stream",
    ) -> str:
        """
        Upload a file to Supabase Storage.

        Args:
            path: Object path within the bucket (e.g. "user_id/filename.pdf").
            data: Raw file bytes.
            content_type: MIME type of the file.

        Returns:
            The storage_path string (same as `path`) for storing in the DB.
        """
        url = f"{self._base_url}/object/{self._bucket}/{path}"
        headers = {**self._headers, "Content-Type": content_type}

        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(url, headers=headers, content=data)
            if resp.status_code not in (200, 201):
                raise RuntimeError(
                    f"Supabase Storage upload failed ({resp.status_code}): {resp.text}"
                )

        return path

    async def get_signed_url(self, storage_path: str, expires_in_seconds: int = 3600) -> str:
        """
        Generate a signed (time-limited) download URL for a stored file.

        Args:
            storage_path: The path returned from upload_file().
            expires_in_seconds: URL validity period (default 1 hour).

        Returns:
            A full HTTPS URL the browser can use to download the file.
        """
        url = f"{self._base_url}/object/sign/{self._bucket}/{storage_path}"
        payload = {"expiresIn": expires_in_seconds}

        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(url, headers=self._headers, json=payload)
            resp.raise_for_status()
            data = resp.json()

        signed_path = data.get("signedURL", "")
        if signed_path.startswith("/"):
            return f"{settings.supabase_url}/storage/v1{signed_path}"
        return f"{self._base_url}/object/sign/{self._bucket}/{signed_path}"

    async def delete_file(self, storage_path: str) -> None:
        """Delete a file from Supabase Storage."""
        url = f"{self._base_url}/object/{self._bucket}/{storage_path}"
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.delete(url, headers=self._headers)
            if resp.status_code not in (200, 204):
                logger.warning(f"Storage delete non-success ({resp.status_code}) for {storage_path}")


# Module-level singleton
storage_adapter = SupabaseStorageAdapter()
