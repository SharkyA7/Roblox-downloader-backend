"""
services/mesh_converter.py
Parse format mesh Roblox (.mesh binary) dan konversi ke OBJ atau GLTF.

Roblox Mesh Versions:
  v1.00  — ASCII
  v2.00  — Binary (triangles + normals + UVs)
  v3.00  — Binary + LOD
  v4.00  — Binary + skinning data
  v5.00  — Binary + skinning + FACS blendshapes
"""
import struct
import json
import io
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class RobloxMesh:
    vertices: list   # list of (x, y, z)
    normals:  list   # list of (nx, ny, nz)
    uvs:      list   # list of (u, v)
    faces:    list   # list of (i0, i1, i2)
    version:  str    = "unknown"
    name:     str    = "mesh"


# ── PARSERS ───────────────────────────────────────────────────────

def _parse_v1(data: bytes) -> RobloxMesh:
    """Version 1.00 — plain ASCII."""
    lines = data.decode("utf-8", errors="replace").splitlines()
    # line 0: version, line 1: face count, line 2+: face data
    faces_raw = []
    verts, norms, uvs, faces = [], [], [], []

    for line in lines[2:]:
        line = line.strip()
        if not line:
            continue
        # Each line is a face: [vx,vy,vz][nx,ny,nz][u,v] repeated 3x
        tokens = line.replace("[", " ").replace("]", " ").split(",")
        floats = [float(t.strip()) for t in tokens if t.strip()]
        # 3 vertices × 8 floats = 24
        if len(floats) < 24:
            continue
        base = len(verts)
        for i in range(3):
            o = i * 8
            verts.append((floats[o],   floats[o+1], floats[o+2]))
            norms.append((floats[o+3], floats[o+4], floats[o+5]))
            uvs.append(  (floats[o+6], floats[o+7]))
        faces.append((base, base+1, base+2))

    return RobloxMesh(verts, norms, uvs, faces, version="1.00")


def _parse_v2(data: bytes) -> RobloxMesh:
    """Version 2.00 — binary with header."""
    buf = io.BytesIO(data)
    # Skip version line  e.g. b'version 2.00\n'
    buf.readline()
    # Header line: sizeof_MeshHeader sizeof_Vertex sizeof_Face
    hdr_line = buf.readline().decode().strip()
    parts = hdr_line.split()
    sizeof_header, sizeof_vertex, sizeof_face = int(parts[0]), int(parts[1]), int(parts[2])

    # Mesh header
    hdr_data = buf.read(sizeof_header)
    nh = (sizeof_header - 4) // 4  # remaining ints after 2-byte lod fields
    num_verts, num_faces = struct.unpack_from("<II", hdr_data, 0)

    verts, norms, uvs, faces = [], [], [], []

    for _ in range(num_verts):
        raw = buf.read(sizeof_vertex)
        # px py pz  nx ny nz  u v  tx ty tz ts (tangent, 4 bytes)
        px, py, pz, nx, ny, nz, u, v = struct.unpack_from("<ffffffff", raw, 0)
        verts.append((px, py, pz))
        norms.append((nx, ny, nz))
        uvs.append((u, 1.0 - v))   # flip V axis

    for _ in range(num_faces):
        raw = buf.read(sizeof_face)
        i0, i1, i2 = struct.unpack_from("<III", raw, 0)
        faces.append((i0, i1, i2))

    return RobloxMesh(verts, norms, uvs, faces, version="2.00")


def _parse_v3(data: bytes) -> RobloxMesh:
    """Version 3.00 — binary + LOD table (we ignore LOD)."""
    buf = io.BytesIO(data)
    buf.readline()  # version
    hdr_line = buf.readline().decode().strip()
    parts = hdr_line.split()
    sizeof_header, sizeof_vertex, sizeof_face, sizeof_lod = (
        int(parts[0]), int(parts[1]), int(parts[2]), int(parts[3])
    )
    hdr_raw = buf.read(sizeof_header)
    num_verts, num_faces, num_lods = struct.unpack_from("<III", hdr_raw, 0)

    verts, norms, uvs, faces = [], [], [], []

    for _ in range(num_verts):
        raw = buf.read(sizeof_vertex)
        px, py, pz, nx, ny, nz, u, v = struct.unpack_from("<ffffffff", raw, 0)
        verts.append((px, py, pz))
        norms.append((nx, ny, nz))
        uvs.append((u, 1.0 - v))

    for _ in range(num_faces):
        raw = buf.read(sizeof_face)
        i0, i1, i2 = struct.unpack_from("<III", raw, 0)
        faces.append((i0, i1, i2))

    return RobloxMesh(verts, norms, uvs, faces, version="3.00")


def parse_mesh(data: bytes, name: str = "mesh") -> RobloxMesh:
    """
    Deteksi versi dan parse mesh Roblox.
    Raises ValueError jika format tidak dikenal.
    """
    if not data:
        raise ValueError("Data mesh kosong")

    header = data[:16].decode("utf-8", errors="replace")

    if "version 1.00" in header:
        mesh = _parse_v1(data)
    elif "version 2.00" in header:
        mesh = _parse_v2(data)
    elif "version 3.00" in header or "version 4.00" in header or "version 5.00" in header:
        # v4 dan v5 memiliki skinning data, kita parse geometry saja seperti v3
        try:
            mesh = _parse_v3(data)
        except Exception:
            # fallback ke v2 parser
            mesh = _parse_v2(data)
    else:
        raise ValueError(f"Format mesh Roblox tidak dikenal: {header[:20]!r}")

    mesh.name = name
    return mesh


# ── EXPORTERS ─────────────────────────────────────────────────────

def mesh_to_obj(mesh: RobloxMesh, mtl_name: Optional[str] = None) -> str:
    """Konversi RobloxMesh ke format OBJ string."""
    lines = [
        f"# Roblox Mesh — {mesh.name}",
        f"# Version: {mesh.version}",
        f"# Vertices: {len(mesh.vertices)}  Faces: {len(mesh.faces)}",
        "",
    ]
    if mtl_name:
        lines += [f"mtllib {mtl_name}.mtl", f"usemtl default", ""]

    lines.append(f"o {mesh.name}")

    for x, y, z in mesh.vertices:
        lines.append(f"v {x:.6f} {y:.6f} {z:.6f}")

    lines.append("")
    for u, v in mesh.uvs:
        lines.append(f"vt {u:.6f} {v:.6f}")

    lines.append("")
    for nx, ny, nz in mesh.normals:
        lines.append(f"vn {nx:.6f} {ny:.6f} {nz:.6f}")

    lines.append("")
    for i0, i1, i2 in mesh.faces:
        # OBJ adalah 1-indexed, format: v/vt/vn
        a, b, c = i0+1, i1+1, i2+1
        lines.append(f"f {a}/{a}/{a} {b}/{b}/{b} {c}/{c}/{c}")

    return "\n".join(lines)


def mesh_to_gltf(mesh: RobloxMesh) -> dict:
    """Konversi RobloxMesh ke GLTF 2.0 dict (bisa di-json.dumps langsung)."""
    import base64

    # Flatten arrays
    pos_data = b""
    for x, y, z in mesh.vertices:
        pos_data += struct.pack("<fff", x, y, z)

    norm_data = b""
    for nx, ny, nz in mesh.normals:
        norm_data += struct.pack("<fff", nx, ny, nz)

    uv_data = b""
    for u, v in mesh.uvs:
        uv_data += struct.pack("<ff", u, v)

    idx_data = b""
    for i0, i1, i2 in mesh.faces:
        idx_data += struct.pack("<III", i0, i1, i2)

    def b64(b: bytes) -> str:
        return "data:application/octet-stream;base64," + base64.b64encode(b).decode()

    n_verts = len(mesh.vertices)
    n_faces = len(mesh.faces)

    min_pos = [min(v[i] for v in mesh.vertices) for i in range(3)]
    max_pos = [max(v[i] for v in mesh.vertices) for i in range(3)]

    gltf = {
        "asset": {"version": "2.0", "generator": "RobloxDownloader/1.0"},
        "scene": 0,
        "scenes": [{"nodes": [0]}],
        "nodes": [{"mesh": 0, "name": mesh.name}],
        "meshes": [{
            "name": mesh.name,
            "primitives": [{
                "attributes": {
                    "POSITION":   0,
                    "NORMAL":     1,
                    "TEXCOORD_0": 2,
                },
                "indices": 3,
                "mode": 4,   # TRIANGLES
            }]
        }],
        "accessors": [
            # 0 POSITION
            {"bufferView": 0, "componentType": 5126, "count": n_verts,
             "type": "VEC3", "min": min_pos, "max": max_pos},
            # 1 NORMAL
            {"bufferView": 1, "componentType": 5126, "count": n_verts, "type": "VEC3"},
            # 2 TEXCOORD_0
            {"bufferView": 2, "componentType": 5126, "count": n_verts, "type": "VEC2"},
            # 3 INDICES
            {"bufferView": 3, "componentType": 5125, "count": n_faces * 3, "type": "SCALAR"},
        ],
        "bufferViews": [
            {"buffer": 0, "byteOffset": 0,                      "byteLength": len(pos_data),  "target": 34962},
            {"buffer": 1, "byteOffset": 0,                      "byteLength": len(norm_data), "target": 34962},
            {"buffer": 2, "byteOffset": 0,                      "byteLength": len(uv_data),   "target": 34962},
            {"buffer": 3, "byteOffset": 0,                      "byteLength": len(idx_data),  "target": 34963},
        ],
        "buffers": [
            {"uri": b64(pos_data),  "byteLength": len(pos_data)},
            {"uri": b64(norm_data), "byteLength": len(norm_data)},
            {"uri": b64(uv_data),   "byteLength": len(uv_data)},
            {"uri": b64(idx_data),  "byteLength": len(idx_data)},
        ],
    }
    return gltf


def default_mtl(name: str = "default") -> str:
    return (
        f"newmtl {name}\n"
        "Ka 0.1 0.1 0.1\n"
        "Kd 0.8 0.8 0.8\n"
        "Ks 0.05 0.05 0.05\n"
        "Ns 10\n"
        "d 1\n"
    )
