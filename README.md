# IMPORTANT ANNOUNCEMENT
Masih dalam tahap pengembangan (BETA)
# Roblox 3D Downloader

Backend FastAPI + Frontend HTML untuk download karakter avatar dan item katalog Roblox dalam format OBJ/GLTF.

## Struktur Project

```
roblox-downloader/
├── backend/
│   ├── main.py                  ← Entry point FastAPI
│   ├── requirements.txt
│   ├── .env.example             ← Template konfigurasi (salin ke .env)
│   ├── routers/
│   │   ├── avatar.py            ← /api/avatar/*
│   │   └── catalog.py           ← /api/catalog/*
│   └── services/
│       ├── roblox.py            ← Semua panggilan ke API Roblox
│       └── mesh_converter.py    ← Parser mesh Roblox → OBJ/GLTF
└── frontend/
    └── index.html               ← UI web (disajikan oleh FastAPI)
```

## Setup & Menjalankan

### 1. Buat Virtual Environment
```bash
cd backend
python -m venv venv
source venv/bin/activate          # Linux/Mac
venv\Scripts\activate             # Windows
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Konfigurasi .env
```bash
cp .env.example .env
# Edit .env dan isi ROBLOX_API_KEY dan ROBLOX_COOKIE
```

**Cara mendapatkan `.ROBLOSECURITY` cookie:**
1. Login ke https://www.roblox.com di browser
2. Buka DevTools (F12) → Application → Cookies → www.roblox.com
3. Cari `.ROBLOSECURITY` → salin value-nya ke `.env`

**Cara mendapatkan Open Cloud API Key:**
1. Buka https://create.roblox.com/settings/api-keys
2. Klik **Create API Key**
3. Pilih scope yang diperlukan → Salin key ke `.env`

### 4. Jalankan Server
```bash
uvicorn main:app --reload --port 8000
```

Buka browser: http://localhost:8000

---

## API Endpoints

| Endpoint | Keterangan |
|----------|-----------|
| `GET /api/avatar/info?user=` | Info profil + data avatar |
| `GET /api/avatar/3d-urls?user=` | URL OBJ/MTL dari Roblox CDN |
| `GET /api/avatar/download?user=&format=` | Download ZIP (OBJ atau GLTF) |
| `GET /api/avatar/wearing?user=` | Daftar asset yang dipakai |
| `GET /api/catalog/info?asset_id=` | Detail item katalog |
| `GET /api/catalog/download?asset_id=&format=` | Download mesh item |
| `GET /api/catalog/raw?asset_id=` | File mentah tanpa konversi |
| `GET /docs` | Swagger UI otomatis |

---

## Format Mesh yang Didukung

| Versi | Format | Status |
|-------|--------|--------|
| v1.00 | ASCII | ✅ |
| v2.00 | Binary | ✅ |
| v3.00 | Binary + LOD | ✅ |
| v4.00 | Binary + Skinning | ✅ (geometry only) |
| v5.00 | Binary + Blendshapes | ✅ (geometry only) |

---

## Penting: Keamanan API Key

- ❌ **JANGAN** taruh API key / cookie di frontend/JavaScript
- ❌ **JANGAN** commit file `.env` ke Git
- ✅ API key hanya ada di server (file `.env`)
- ✅ Untuk production: gunakan environment variables hosting (Railway, Render, dll)
- ✅ Tambah rate limiting untuk mencegah penyalahgunaan

---

## Deploy ke Production (Render.com / Railway)

1. Push code ke GitHub (pastikan `.env` ada di `.gitignore`)
2. Di dashboard Render/Railway → tambah environment variables:
   - `ROBLOX_API_KEY` = key Anda
   - `ROBLOX_COOKIE` = cookie Anda
3. Start command: `uvicorn main:app --host 0.0.0.0 --port $PORT`
