# ROKKUS AI Inventory Assistant (GenAI Module)

Modul layanan Generative AI untuk aplikasi **ROKKUS Mardani Raya** (Pengelolaan dan Pemantauan Stok Harian Terintegrasi).

> **CATATAN PROTOTIPE**:
> Layanan pada tahap ini beroperasi dalam mode **Mock Provider** menggunakan dataset dan input sintetis/ilustratif. Layanan ini dirancang menggunakan antarmuka modular (*Hexagonal Architecture*) sehingga siap beralih ke **Google Gemini API** segera setelah API key dan dataset resmi tersedia.

---

## Aturan Konsisten Status Stok

Klasifikasi status ketersediaan barang dihitung secara otomatis berdasarkan aturan pada `src/core/rules.py`:

| Status | Formula Kondisi | Makna Operasional UMKM ROKKUS |
| :--- | :--- | :--- |
| **`CRITICAL`** | `current_stock <= minimum_stock` | Stok berada pada atau di bawah batas minimum. Memerlukan **restock segera** agar produksi tidak terhenti. |
| **`WARNING`** | `minimum_stock < current_stock <= (minimum_stock * 1.5)` | Stok mendekati batas minimum (100% - 150%). Perlu dipantau dan dijadwalkan pemesanan ulang ke supplier. |
| **`SAFE`** | `current_stock > (minimum_stock * 1.5)` | Stok melampaui 150% batas minimum. Kondisi aman untuk operasional harian. |

> **Perilaku Khusus `minimum_stock = 0`**:
> - Jika `current_stock = 0` dan `minimum_stock = 0`: `current_stock <= minimum_stock` bernilai `True` sehingga statusnya **`CRITICAL`** (barang habis).
> - Jika `current_stock > 0` dan `minimum_stock = 0`: Barang langsung berstatus **`SAFE`** karena `0 * 1.5 = 0` (tidak ada zona `WARNING` numerik pada batas minimum nol).

---

## Struktur Direktori

```text
ai/genai/
├── requirements.txt             # Dependensi modul AI Assistant
├── .env.example                 # Template environment variables
├── data/
│   └── synthetic_inventory.json # Data sintetis ilustratif (bukan data riil)
├── src/
│   ├── main.py                  # Entrypoint aplikasi FastAPI
│   ├── core/
│   │   ├── config.py            # Pengaturan aplikasi & path resolver
│   │   └── rules.py             # Definisi aturan SAFE, WARNING, CRITICAL
│   ├── schemas/
│   │   ├── chat.py              # DTO Request & Response interaksi chat
│   │   ├── inventory.py         # DTO data barang & transaksi
│   │   └── summary.py           # DTO Request & Response Daily Stock Summary
│   ├── repositories/
│   │   ├── base.py              # Abstract Base Inventory Repository
│   │   └── mock_inventory.py    # Repository pembaca JSON lokal
│   ├── services/
│   │   ├── llm_base.py          # Abstract Base LLM Service
│   │   ├── mock_llm.py          # Generator respons mock berbasis aturan & data
│   │   ├── assistant_service.py # Orchestrator chat assistant
│   │   └── summary_service.py   # Service ringkasan stok harian (Mock Engine)
│   └── api/
│       └── v1/
│           ├── router.py        # Agregator router API v1
│           └── endpoints/
│               ├── health.py    # GET /api/v1/health
│               ├── chat.py      # POST /api/v1/assistant/chat
│               └── summary.py   # POST /api/v1/summary/daily
└── tests/
    ├── conftest.py              # Fixture pytest & path import
    ├── test_stock_rules.py      # Unit test aturan stok & minimum_stock = 0
    ├── test_mock_inventory.py   # Unit test repository & dataset sintetis
    ├── test_mock_llm.py         # Unit test logika respons mock chat & provider
    ├── test_endpoints.py        # Integration test endpoint HTTP v1
    └── test_daily_summary.py    # Unit & integration test Daily Stock Summary
```

---

## Endpoint API Utama

### 1. Daily Stock Summary: `POST /api/v1/summary/daily`
Menerima payload JSON data stok harian, mengklasifikasi status item secara konsisten, dan menyusun narasi ringkasan stok bahasa Indonesia berbasis data faktual tanpa estimasi spekulatif.

#### Contoh Request:
```bash
curl -X POST "http://127.0.0.1:8001/api/v1/summary/daily" \
     -H "Content-Type: application/json" \
     -d '{
       "date": "2026-11-15",
       "store_name": "UMKM ROKKUS Mardani Raya",
       "items": [
         {
           "name": "Tepung Terigu Protein Sedang",
           "current_stock": 4.0,
           "minimum_stock": 10.0,
           "unit": "kg",
           "category": "bahan_baku"
         },
         {
           "name": "Margarin Bakeri Spesial",
           "current_stock": 8.0,
           "minimum_stock": 6.0,
           "unit": "kg",
           "category": "bahan_baku"
         },
         {
           "name": "Gula Pasir Tebu",
           "current_stock": 20.0,
           "minimum_stock": 10.0,
           "unit": "kg",
           "category": "bahan_baku"
         }
       ]
     }'
```

#### Contoh Response:
```json
{
  "status": "success",
  "data": {
    "date": "2026-11-15",
    "store_name": "UMKM ROKKUS Mardani Raya",
    "summary": "Ringkasan Stok Harian (2026-11-15) untuk UMKM ROKKUS Mardani Raya: Dari total 3 barang yang dipantau, tercatat 1 barang berstatus CRITICAL, 1 barang berstatus WARNING, dan 1 barang berstatus SAFE. Perhatian mendesak diperlukan pada item berstatus kritis: Tepung Terigu Protein Sedang (sisa 4.0 kg, min: 10.0 kg). Barang-barang ini berada pada atau di bawah batas minimum dan membutuhkan pengadaan ulang segera. Item pada zona waspada yang perlu dipantau ketat: Margarin Bakeri Spesial (sisa 8.0 kg, min: 6.0 kg). Sebanyak 1 barang lainnya berada dalam kondisi stok aman untuk operasional.",
    "status_counts": {
      "critical": 1,
      "warning": 1,
      "safe": 1,
      "total_items": 3
    },
    "items": [
      {
        "id": null,
        "name": "Tepung Terigu Protein Sedang",
        "category": "bahan_baku",
        "current_stock": 4.0,
        "minimum_stock": 10.0,
        "unit": "kg",
        "status": "CRITICAL",
        "status_description": "Stok sama atau di bawah batas minimum (current <= min). Butuh restock darurat."
      },
      {
        "id": null,
        "name": "Margarin Bakeri Spesial",
        "category": "bahan_baku",
        "current_stock": 8.0,
        "minimum_stock": 6.0,
        "unit": "kg",
        "status": "WARNING",
        "status_description": "Stok mendekati batas minimum (min < current <= min * 1.5). Pantau & rencanakan restock."
      },
      {
        "id": null,
        "name": "Gula Pasir Tebu",
        "category": "bahan_baku",
        "current_stock": 20.0,
        "minimum_stock": 10.0,
        "unit": "kg",
        "status": "SAFE",
        "status_description": "Stok mencukupi untuk operasional (current > min * 1.5). Kondisi aman."
      }
    ],
    "suggested_actions": [
      "Lakukan pemesanan ulang (restock) darurat hari ini untuk: Tepung Terigu Protein Sedang.",
      "Lakukan pengecekan fisik dan koordinasi jadwal pengadaan untuk item waspada: Margarin Bakeri Spesial.",
      "Pertahankan rotasi barang menggunakan metode FIFO (First In First Out)."
    ],
    "meta": {
      "provider": "mock",
      "is_synthetic": true,
      "source": "synthetic_input",
      "disclaimer": "PERINGATAN: Ringkasan ini dihasilkan oleh Mock Service menggunakan data sintetis/ilustratif untuk prototipe ROKKUS, bukan data operasional nyata UMKM.",
      "generated_at": "2026-11-15T08:43:54.409564+00:00"
    }
  }
}
```

---

## Panduan Menjalankan Layanan Secara Lokal

### 1. Menyiapkan Virtual Environment
```bash
cd ai/genai
python -m venv .venv

# Windows (PowerShell):
.venv\Scripts\Activate.ps1

# Linux / macOS:
source .venv/bin/activate
```

### 2. Menginstal Dependensi
```bash
pip install -r requirements.txt
```

### 3. Menjalankan Server FastAPI
```bash
uvicorn src.main:app --host 127.0.0.1 --port 8001 --reload
```
Akses dokumentasi interaktif:
* **Swagger UI**: [http://127.0.0.1:8001/docs](http://127.0.0.1:8001/docs)
* **ReDoc**: [http://127.0.0.1:8001/redoc](http://127.0.0.1:8001/redoc)
* **Health Check**: [http://127.0.0.1:8001/api/v1/health](http://127.0.0.1:8001/api/v1/health)

---

## Menjalankan Pengujian (Testing)

Jalankan test suite menggunakan pytest di dalam virtual environment:
```bash
# Menjalankan seluruh pengujian:
pytest tests/ -v

# Menjalankan pengujian fitur ringkasan harian:
pytest tests/test_daily_summary.py -v
```
Semua 30 pengujian dirancang untuk memverifikasi fungsionalitas normal, edge cases (input kosong, stok negatif, angka non-finite, validasi tanggal kalender), serta konsistensi aturan status stok.
