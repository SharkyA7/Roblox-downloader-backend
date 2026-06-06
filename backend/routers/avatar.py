"""
routers/avatar.py
Endpoints untuk download avatar pemain 3D.
"""
import io
import asyncio
import zipfile
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse, JSONResponse

from services import roblox
from services.mesh_converter import default_mtl

router = APIRouter()


async def _resolve(username_or_id: str) -> int:
    """Terima username atau numeric ID, selalu kembalikan user_id int."""
    if username_or_id.strip().isdigit():
        return int(username_or_id.strip())
    uid = await roblox.username_to_id(username_or_id.strip())
    if not uid:
        raise HTTPException(404, f"Username '{username_or_id}' tidak ditemukan di Roblox.")
    return uid


# ── GET /api/avatar/info ──────────────────────────────────────────
@router.get("/info")
async def avatar_info(user: str = Query(..., description="Username atau User ID")):
    """
    Kembalikan info lengkap avatar:
    - Data user (nama, ID, created)
    - Body colors, scales, rig type
    - Daftar aset yang dipakai
    - URL thumbnail 2D
    """
    uid = await _resolve(user)
    user_info, avatar_data, thumb_url = await asyncio.gather(
        roblox.get_user_info(uid),
        roblox.get_avatar_info(uid),
        roblox.get_avatar_thumbnail_2d(uid),
    )
    return {
        "userId":       uid,
        "username":     user_info.get("name"),
        "displayName":  user_info.get("displayName"),
        "created":      user_info.get("created"),
        "description":  user_info.get("description"),
        "profileUrl":   f"https://www.roblox.com/users/{uid}/profile",
        "thumbnailUrl": thumb_url,
        "rigType":      avatar_data.get("playerAvatarType"),
        "scales":       avatar_data.get("scales"),
        "bodyColors":   avatar_data.get("bodyColors"),
        "assets":       avatar_data.get("assets", []),
    }


# ── GET /api/avatar/3d-urls ───────────────────────────────────────
@router.get("/3d-urls")
async def avatar_3d_urls(
    user: str = Query(..., description="Username atau User ID"),
    retries: int = Query(6, ge=1, le=10, description="Jumlah retry jika thumbnail belum siap"),
):
    """
    Kembalikan URL .obj dan .mtl dari Roblox CDN.
    Roblox men-generate thumbnail secara async — otomatis retry jika Pending.
    """
    uid = await _resolve(user)

    manifest_url = None
    for attempt in range(retries):
        manifest_url = await roblox.get_avatar_3d_manifest_url(uid)
        if manifest_url:
            break
        if attempt < retries - 1:
            await asyncio.sleep(3)

    if not manifest_url:
        raise HTTPException(
            503,
            detail={
                "error": "3D thumbnail belum siap atau tidak tersedia.",
                "hints": [
                    "Avatar mungkin menggunakan rig R6 (hanya R15 yang didukung Roblox untuk 3D export).",
                    "Coba lagi dalam 10–30 detik.",
                    "Pastikan profil tidak di-private.",
                ],
            }
        )

    manifest = await roblox.get_avatar_3d_manifest(manifest_url)
    return {
        "userId":      uid,
        "manifestUrl": manifest_url,
        "objUrl":      manifest.get("obj"),
        "mtlUrl":      manifest.get("mtl"),
        "textures":    manifest.get("textures", []),
        "camera":      manifest.get("camera"),
    }


# ── GET /api/avatar/download ──────────────────────────────────────
@router.get("/download")
async def avatar_download(
    user:   str = Query(..., description="Username atau User ID"),
    format: str = Query("obj", description="Format: 'obj' atau 'gltf'"),
):
    """
    Download avatar 3D sebagai file ZIP.
    - OBJ mode : ZIP berisi avatar.obj + avatar.mtl
    - GLTF mode: ZIP berisi avatar.gltf
    """
    uid = await _resolve(user)

    # Ambil 3D manifest URL dengan retry
    manifest_url = None
    for attempt in range(6):
        manifest_url = await roblox.get_avatar_3d_manifest_url(uid)
        if manifest_url:
            break
        await asyncio.sleep(3)

    if not manifest_url:
        raise HTTPException(503, "3D thumbnail tidak tersedia untuk avatar ini.")

    manifest = await roblox.get_avatar_3d_manifest(manifest_url)
    obj_url = manifest.get("obj")
    mtl_url = manifest.get("mtl")

    if not obj_url:
        raise HTTPException(502, "Manifest tidak mengandung URL OBJ.")

    # Download file dari Roblox CDN
    obj_bytes, mtl_bytes = await asyncio.gather(
        roblox.download_obj_file(obj_url),
        roblox.download_mtl_file(mtl_url) if mtl_url else asyncio.coroutine(lambda: b"")(),
    )

    # Ambil username untuk nama file
    try:
        info = await roblox.get_user_info(uid)
        fname = info.get("name", str(uid))
    except Exception:
        fname = str(uid)

    # Buat ZIP
    zip_buf = io.BytesIO()
    with zipfile.ZipFile(zip_buf, "w", zipfile.ZIP_DEFLATED) as zf:
        if format.lower() == "gltf":
            # Konversi OBJ → sederhana (embed OBJ sebagai GLTF placeholder)
            # Untuk konversi penuh gunakan Blender CLI atau blender-asset-tracer
            zf.writestr(f"{fname}.obj", obj_bytes)
            zf.writestr(f"{fname}.mtl", mtl_bytes or default_mtl())
            zf.writestr("README.txt", (
                "File OBJ dan MTL disertakan.\n"
                "Untuk mengkonversi ke GLTF:\n"
                "  1. Buka Blender → File → Import → Wavefront OBJ\n"
                "  2. File → Export → glTF 2.0\n"
                "Atau gunakan: https://products.aspose.app/3d/conversion/obj-to-gltf"
            ))
        else:
            zf.writestr(f"{fname}.obj", obj_bytes)
            if mtl_bytes:
                zf.writestr(f"{fname}.mtl", mtl_bytes)

    zip_buf.seek(0)
    return StreamingResponse(
        zip_buf,
        media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="{fname}_avatar.zip"'},
    )


# ── GET /api/avatar/wearing ───────────────────────────────────────
@router.get("/wearing")
async def avatar_wearing(user: str = Query(...)):
    """Daftar Asset ID yang saat ini dipakai avatar."""
    uid = await _resolve(user)
    asset_ids = await roblox.get_currently_wearing(uid)
    return {"userId": uid, "assetIds": asset_ids, "count": len(asset_ids)}
