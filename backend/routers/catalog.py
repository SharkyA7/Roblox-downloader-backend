"""
routers/catalog.py
Endpoints untuk info dan download item katalog Roblox (.rbxm → OBJ/GLTF).
"""
import io
import json
import zipfile
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse

from services import roblox
from services.mesh_converter import parse_mesh, mesh_to_obj, mesh_to_gltf, default_mtl

router = APIRouter()

SUPPORTED_ASSET_TYPES = {
    2:  "T-Shirt",
    11: "Shirt",
    12: "Pants",
    17: "Head",
    18: "Face",
    19: "Gear",
    41: "Hair Accessory",
    42: "Face Accessory",
    43: "Neck Accessory",
    44: "Shoulder Accessory",
    45: "Front Accessory",
    46: "Back Accessory",
    47: "Waist Accessory",
    48: "Climb Animation",
    61: "MeshPart",
    62: "LayeredClothing",
}


# ── GET /api/catalog/info ─────────────────────────────────────────
@router.get("/info")
async def catalog_info(asset_id: int = Query(..., description="Asset ID dari URL katalog Roblox")):
    """
    Kembalikan detail item katalog: nama, tipe, deskripsi, harga, thumbnail.
    """
    details, thumbnail = await __import__("asyncio").gather(
        roblox.get_asset_details(asset_id),
        roblox.get_asset_thumbnail(asset_id),
    )
    if not details:
        raise HTTPException(404, f"Asset ID {asset_id} tidak ditemukan.")

    asset_type_id = details.get("assetType")
    return {
        "assetId":      asset_id,
        "name":         details.get("name"),
        "description":  details.get("description"),
        "assetType":    SUPPORTED_ASSET_TYPES.get(asset_type_id, f"Type {asset_type_id}"),
        "assetTypeId":  asset_type_id,
        "creatorName":  details.get("creatorName"),
        "price":        details.get("price"),
        "thumbnailUrl": thumbnail,
        "catalogUrl":   f"https://www.roblox.com/catalog/{asset_id}",
    }


# ── GET /api/catalog/download ─────────────────────────────────────
@router.get("/download")
async def catalog_download(
    asset_id: int = Query(..., description="Asset ID item katalog"),
    format:   str = Query("obj", description="Format output: 'obj' atau 'gltf'"),
):
    """
    Download item katalog sebagai OBJ atau GLTF dalam ZIP.
    Backend men-download file .mesh binary dari Roblox CDN,
    memparsing geometri, lalu mengekspor ke format yang diminta.
    """
    # Ambil info item
    details = await roblox.get_asset_details(asset_id)
    if not details:
        raise HTTPException(404, f"Asset ID {asset_id} tidak ditemukan.")

    item_name = details.get("name", str(asset_id))
    safe_name = "".join(c if c.isalnum() or c in " _-" else "_" for c in item_name).strip()

    # Download raw asset bytes dari CDN
    try:
        raw_bytes = await roblox.download_asset_raw(asset_id)
    except Exception as e:
        raise HTTPException(502, f"Gagal download asset dari Roblox CDN: {e}")

    if not raw_bytes:
        raise HTTPException(502, "Asset kosong atau tidak dapat diakses.")

    # Deteksi apakah ini file mesh Roblox atau format lain
    header = raw_bytes[:20]
    is_mesh = header.startswith(b"version") or b"version 1" in header or b"version 2" in header

    zip_buf = io.BytesIO()
    with zipfile.ZipFile(zip_buf, "w", zipfile.ZIP_DEFLATED) as zf:

        if is_mesh:
            # Parse dan konversi mesh
            try:
                mesh = parse_mesh(raw_bytes, name=safe_name)
            except ValueError as e:
                # Simpan raw + error note jika parse gagal
                zf.writestr(f"{safe_name}.mesh", raw_bytes)
                zf.writestr("ERROR.txt", (
                    f"Gagal parse mesh: {e}\n\n"
                    "File .mesh mentah disertakan.\n"
                    "Anda bisa coba import ke Blender menggunakan plugin:\n"
                    "https://github.com/MaximumADHD/Roblox-Mesh-Format"
                ))
            else:
                if format.lower() == "gltf":
                    gltf_dict = mesh_to_gltf(mesh)
                    zf.writestr(f"{safe_name}.gltf", json.dumps(gltf_dict, indent=2))
                else:
                    obj_text  = mesh_to_obj(mesh, mtl_name=safe_name)
                    mtl_text  = default_mtl()
                    zf.writestr(f"{safe_name}.obj", obj_text)
                    zf.writestr(f"{safe_name}.mtl", mtl_text)

        else:
            # Bukan mesh standar — simpan raw untuk dibuka manual
            # (bisa jadi .rbxm XML, PNG texture, dll.)
            ext = _guess_extension(raw_bytes)
            zf.writestr(f"{safe_name}{ext}", raw_bytes)
            zf.writestr("README.txt", (
                f"Asset ID: {asset_id}\n"
                f"Nama: {item_name}\n\n"
                f"File ini bukan format mesh standar (format: {ext}).\n"
                "Untuk .rbxm: buka di Roblox Studio → Import Model.\n"
                "Untuk gambar: gunakan langsung sebagai tekstur."
            ))

    zip_buf.seek(0)
    return StreamingResponse(
        zip_buf,
        media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="{safe_name}.zip"'},
    )


# ── GET /api/catalog/raw ──────────────────────────────────────────
@router.get("/raw")
async def catalog_raw(asset_id: int = Query(...)):
    """
    Download file mentah (.mesh/.rbxm/dll) tanpa konversi.
    Berguna untuk debugging atau penggunaan di Roblox Studio.
    """
    try:
        raw_bytes = await roblox.download_asset_raw(asset_id)
    except Exception as e:
        raise HTTPException(502, f"Gagal download: {e}")

    ext  = _guess_extension(raw_bytes)
    mime = {
        ".mesh": "application/octet-stream",
        ".rbxm": "application/xml",
        ".png":  "image/png",
        ".jpg":  "image/jpeg",
    }.get(ext, "application/octet-stream")

    return StreamingResponse(
        io.BytesIO(raw_bytes),
        media_type=mime,
        headers={"Content-Disposition": f'attachment; filename="asset_{asset_id}{ext}"'},
    )


def _guess_extension(data: bytes) -> str:
    if data[:4] == b"\x89PNG":    return ".png"
    if data[:2] == b"\xff\xd8":   return ".jpg"
    if data[:4] == b"PK\x03\x04": return ".zip"
    if data[:5] == b"<?xml":      return ".rbxm"
    if b"version" in data[:16]:   return ".mesh"
    return ".bin"
