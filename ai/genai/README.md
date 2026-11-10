# ROKKUS AI Inventory Assistant (GenAI Module)

Modul layanan Generative AI untuk aplikasi **ROKKUS Mardani Raya** (Pengelolaan dan Pemantauan Stok Harian Terintegrasi).

> **CATATAN PROTOTIPE**:
> Layanan pada tahap ini beroperasi dalam mode **Mock Provider** menggunakan dataset sintetis/ilustratif (`data/synthetic_inventory.json`). Layanan ini dirancang menggunakan antarmuka modular (*Hexagonal Architecture*) sehingga siap beralih ke **Google Gemini API** segera setelah API key tersedia.

---

## Aturan Konsisten Status Stok

Klasifikasi status ketersediaan barang dihitung secara otomatis berdasarkan aturan:

| Status | Formula Kondisi | Makna Operasional |
| :--- | :--- | :--- |
| **`CRITICAL`** | `current_stock <= minimum_stock` | Stok berada pada atau di bawah batas minimum. Memerlukan **restock segera** agar produksi tidak terhenti. |
| **`WARNING`** | `minimum_stock < current_stock <= (minimum_stock * 1.5)` | Stok mendekati batas minimum (100% - 150%). Perlu dipantau dan dijadwalkan pemesanan ulang ke supplier. |
| **`SAFE`** | `current_stock > (minimum_stock * 1.5)` | Stok melampaui 150% batas minimum. Kondisi aman untuk operasional harian. |

---

## Struktur Direktori

```text
ai/genai/
├── requirements.txt           # Dependensi modul AI Assistant
├── .env.example               # Template environment variables
├── data/
│   └── synthetic_inventory.json # Data sintetis ilustratif (bukan data riil)
├── src/
│   ├── main.py                # Entrypoint aplikasi FastAPI
│   ├── core/
│   │   ├── config.py          # Pengaturan aplikasi & path resolver
│   │   └── rules.py           # Definisi aturan SAFE, WARNING, CRITICAL
│   ├── schemas/
│   │   ├── chat.py            # DTO Request & Response (provider: "mock")
│   │   └── inventory.py       # DTO data barang & transaksi
│   ├── repositories/
│   │   ├── base.py            # Abstract Base Inventory Repository
│   │   └── mock_inventory.py  # Repository pembaca JSON lokal
│   ├── services/
│   │   ├── llm_base.py        # Abstract Base LLM Service
│   │   ├── mock_llm.py        # Generator respons mock berbasis aturan & data
│   │   └── assistant_service.py # Orchestrator penyuntik konteks ke LLM
│   └── api/
│       └── v1/
│           ├── router.py      # Agregator router API v1
│           └── endpoints/
│               ├── health.py  # GET /api/v1/health
│               └── chat.py    # POST /api/v1/assistant/chat
└── tests/
    ├── conftest.py            # Fixture pytest
    ├── test_stock_rules.py    # Unit test aturan stok
    ├── test_mock_inventory.py # Unit test repository & dataset sintetis
    ├── test_mock_llm.py       # Unit test logika respons mock & provider
    └── test_endpoints.py      # Integration test endpoint HTTP
```

---

## Panduan Menjalankan Layanan Secara Lokal

### 1. Menyiapkan Virtual Environment (Rekomendasi)
Buka terminal di root repository atau direktori `ai/genai`:
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

### 3. Mengatur Environment Variables
Salin file `.env.example` menjadi `.env`:
```bash
cp .env.example .env
```

### 4. Menjalankan Server FastAPI
Jalankan server menggunakan Uvicorn:
```bash
uvicorn src.main:app --host 127.0.0.1 --port 8001 --reload
```
Akses dokumentasi interaktif:
* **Swagger UI**: [http://127.0.0.1:8001/docs](http://127.0.0.1:8001/docs)
* **ReDoc**: [http://127.0.0.1:8001/redoc](http://127.0.0.1:8001/redoc)
* **Health Check**: [http://127.0.0.1:8001/api/v1/health](http://127.0.0.1:8001/api/v1/health)

---

## Menjalankan Pengujian (Testing)

### Menggunakan Pytest:
```bash
pytest tests/ -v
```

### Menggunakan Python Unittest (Bawaan Standard Library):
```bash
python -m unittest discover -s tests -p "test_*.py" -v
```

