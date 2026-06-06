"""
services/roblox.py
Semua panggilan ke Roblox API dilakukan di sini.
API key / cookie TIDAK pernah dikirim ke frontend.
"""
import os
import httpx
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

COOKIE    = os.getenv("ROBLOX_COOKIE", "")
API_KEY   = os.getenv("ROBLOX_API_KEY", "")
TIMEOUT   = 20.0

def _headers(auth: bool = False) -> dict:
    h = {
        "Accept":     "application/json",
        "User-Agent": "RobloxDownloader/1.0",
    }
    if auth and COOKIE:
        h["Cookie"] = f".ROBLOSECURITY={COOKIE}"
    if auth and API_KEY:
        h["x-api-key"] = API_KEY
    return h


# ── USER ──────────────────────────────────────────────────────────

async def username_to_id(username: str) -> Optional[int]:
    url  = "https://users.roblox.com/v1/usernames/users"
    body = {"usernames": [username], "excludeBannedUsers": False}
    async with httpx.AsyncClient(timeout=TIMEOUT) as c:
        r = await c.post(url, json=body, headers=_headers())
        r.raise_for_status()
        data = r.json().get("data", [])
        return data[0]["id"] if data else None


async def get_user_info(user_id: int) -> dict:
    url = f"https://users.roblox.com/v1/users/{user_id}"
    async with httpx.AsyncClient(timeout=TIMEOUT) as c:
        r = await c.get(url, headers=_headers())
        r.raise_for_status()
        return r.json()


# ── AVATAR ────────────────────────────────────────────────────────

async def get_avatar_info(user_id: int) -> dict:
    """Body colors, scales, asset list, rig type."""
    url = f"https://avatar.roblox.com/v1/users/{user_id}/avatar"
    async with httpx.AsyncClient(timeout=TIMEOUT) as c:
        r = await c.get(url, headers=_headers())
        r.raise_for_status()
        return r.json()


async def get_currently_wearing(user_id: int) -> list[int]:
    """List of asset IDs currently worn by the avatar."""
    url = f"https://avatar.roblox.com/v1/users/{user_id}/currently-wearing"
    async with httpx.AsyncClient(timeout=TIMEOUT) as c:
        r = await c.get(url, headers=_headers())
        r.raise_for_status()
        return r.json().get("assetIds", [])


async def get_avatar_thumbnail_2d(user_id: int) -> Optional[str]:
    url = (
        f"https://thumbnails.roblox.com/v1/users/avatar"
        f"?userIds={user_id}&size=420x420&format=Png"
    )
    async with httpx.AsyncClient(timeout=TIMEOUT) as c:
        r = await c.get(url, headers=_headers())
        if not r.is_success:
            return None
        data = r.json().get("data", [])
        return data[0].get("imageUrl") if data else None


async def get_avatar_3d_manifest_url(user_id: int) -> Optional[str]:
    """
    Returns the URL of the JSON manifest that contains .obj/.mtl links.
    Roblox generates this lazily — caller should retry a few times.
    """
    url = f"https://thumbnails.roblox.com/v1/users/avatar-3d?userId={user_id}"
    async with httpx.AsyncClient(timeout=TIMEOUT) as c:
        r = await c.get(url, headers=_headers())
        if not r.is_success:
            return None
        data = r.json().get("data", [])
        if not data:
            return None
        item = data[0]
        if item.get("state") == "Completed":
            return item.get("imageUrl")
        return None


async def get_avatar_3d_manifest(manifest_url: str) -> dict:
    """Fetch the manifest JSON that has .obj and .mtl URLs."""
    async with httpx.AsyncClient(timeout=TIMEOUT) as c:
        r = await c.get(manifest_url, headers=_headers())
        r.raise_for_status()
        return r.json()


async def download_obj_file(obj_url: str) -> bytes:
    async with httpx.AsyncClient(timeout=30.0) as c:
        r = await c.get(obj_url, headers=_headers())
        r.raise_for_status()
        return r.content


async def download_mtl_file(mtl_url: str) -> bytes:
    async with httpx.AsyncClient(timeout=30.0) as c:
        r = await c.get(mtl_url, headers=_headers())
        r.raise_for_status()
        return r.content


# ── ASSET / CATALOG ───────────────────────────────────────────────

async def get_asset_details(asset_id: int) -> dict:
    """Get catalog item details (name, type, description, thumbnail)."""
    url = "https://catalog.roblox.com/v1/catalog/items/details"
    body = {"items": [{"itemType": "Asset", "id": asset_id}]}
    async with httpx.AsyncClient(timeout=TIMEOUT) as c:
        r = await c.post(url, json=body, headers=_headers())
        r.raise_for_status()
        data = r.json().get("data", [])
        return data[0] if data else {}


async def get_asset_thumbnail(asset_id: int) -> Optional[str]:
    url = (
        f"https://thumbnails.roblox.com/v1/assets"
        f"?assetIds={asset_id}&size=420x420&format=Png"
    )
    async with httpx.AsyncClient(timeout=TIMEOUT) as c:
        r = await c.get(url, headers=_headers())
        if not r.is_success:
            return None
        data = r.json().get("data", [])
        return data[0].get("imageUrl") if data else None


async def download_asset_raw(asset_id: int) -> bytes:
    """
    Downloads the raw asset file from Roblox CDN.
    Requires .ROBLOSECURITY cookie for non-public assets.
    Returns raw bytes (usually a .rbxm binary or mesh file).
    """
    url = f"https://assetdelivery.roblox.com/v1/asset/?id={asset_id}"
    async with httpx.AsyncClient(
        timeout=30.0,
        follow_redirects=True,
    ) as c:
        r = await c.get(url, headers=_headers(auth=True))
        r.raise_for_status()
        return r.content


async def get_asset_download_url(asset_id: int) -> Optional[str]:
    """Get CDN download URL for an asset (may redirect)."""
    url = f"https://assetdelivery.roblox.com/v2/asset/?id={asset_id}"
    async with httpx.AsyncClient(timeout=TIMEOUT) as c:
        r = await c.get(url, headers=_headers(auth=True))
        if not r.is_success:
            return None
        data = r.json()
        locations = data.get("locations", [])
        return locations[0].get("location") if locations else None
