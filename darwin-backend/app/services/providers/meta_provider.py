from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any, Optional

import httpx
from dotenv import load_dotenv

load_dotenv()


class MetaAPIError(RuntimeError):
    def __init__(self, status_code: int, payload: Any):
        super().__init__("Meta Graph API error")
        self.status_code = status_code
        self.payload = payload


def _require(name: str) -> str:
    v = os.getenv(name)
    if not v:
        raise RuntimeError(f"{name} no está definido en el entorno")
    return v


@dataclass
class MetaProvider:
    api_version: str
    page_id: str
    access_token: str

    @property
    def base_url(self) -> str:
        return f"https://graph.facebook.com/{self.api_version}"

    async def publish_variant(self, *, message: str) -> dict[str, Any]:
        """
        Publica un post en la Facebook Page: POST /{page_id}/feed
        Retorna: { post_id, post_url, raw }
        """
        url = f"{self.base_url}/{self.page_id}/feed"

        async with httpx.AsyncClient(timeout=30.0) as client:
            r = await client.post(
                url,
                data={
                    "message": message,
                    "access_token": self.access_token,
                },
            )

            payload = r.json() if r.headers.get("content-type", "").startswith("application/json") else r.text
            if r.status_code >= 400:
                raise MetaAPIError(r.status_code, payload)

            post_id = payload.get("id")
            post_url: Optional[str] = None

            # Mejor esfuerzo: pedir permalink_url del post
            if post_id:
                r2 = await client.get(
                    f"{self.base_url}/{post_id}",
                    params={"fields": "permalink_url", "access_token": self.access_token},
                )
                if r2.status_code < 400:
                    p2 = r2.json()
                    post_url = p2.get("permalink_url")

            return {"post_id": post_id, "post_url": post_url, "raw": payload}

    async def delete_post(self, *, post_id: str) -> dict[str, Any]:
        """
        Borra un post: DELETE /{post_id}
        Retorna payload de Meta (normalmente {"success": true})
        """
        url = f"{self.base_url}/{post_id}"

        async with httpx.AsyncClient(timeout=30.0) as client:
            r = await client.delete(url, params={"access_token": self.access_token})

            payload = r.json() if r.headers.get("content-type", "").startswith("application/json") else r.text
            if r.status_code >= 400:
                raise MetaAPIError(r.status_code, payload)

            return {"raw": payload}
            
    async def fetch_post_counts(self, *, post_id: str) -> dict[str, int]:
        """
        Trae conteos básicos del post:
          shares.count
          likes.summary.total_count (o reactions.summary.total_count como fallback)
          comments.summary.total_count
        """
        url = f"{self.base_url}/{post_id}"
        fields = "shares,likes.limit(0).summary(true),comments.limit(0).summary(true),reactions.limit(0).summary(true)"

        async with httpx.AsyncClient(timeout=30.0) as client:
            r = await client.get(
                url,
                params={
                    "fields": fields,
                    "access_token": self.access_token,
                },
            )

            payload = r.json() if r.headers.get("content-type", "").startswith("application/json") else r.text
            if r.status_code >= 400:
                raise MetaAPIError(r.status_code, payload)

            shares = int((payload.get("shares") or {}).get("count") or 0)

            likes_obj = payload.get("likes") or {}
            likes = int(((likes_obj.get("summary") or {}).get("total_count")) or 0)

            # Fallback: a veces “likes” no viene pero “reactions” sí
            if likes == 0:
                reactions_obj = payload.get("reactions") or {}
                likes = int(((reactions_obj.get("summary") or {}).get("total_count")) or 0)

            comments_obj = payload.get("comments") or {}
            comments = int(((comments_obj.get("summary") or {}).get("total_count")) or 0)

            return {
                "shares": shares,
                "likes": likes,
                "comments": comments,
            }
      


def get_meta_provider() -> MetaProvider:
    return MetaProvider(
        api_version=os.getenv("META_API_VERSION", "v25.0"),
        page_id=_require("META_PAGE_ID"),
        access_token=_require("META_PAGE_ACCESS_TOKEN"),
    )