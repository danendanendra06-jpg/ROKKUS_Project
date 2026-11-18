# ROKKUS AI Inventory Assistant (GenAI Module)

Modul layanan Generative AI untuk aplikasi **ROKKUS Mardani Raya** (Pengelolaan dan Pemantauan Stok Harian Terintegrasi).

> **CATATAN TAHAP 4 (GEMINI API INTEGRATION READY)**:
> Layanan telah terintegrasi dengan **Google Gen AI SDK resmi (`google-genai`)** menggunakan asynchronous API, timeout, dan *Factory Provider*. Sistem mendukung peralihan mulus antara mode **Mock** dan **Gemini**, serta selalu dilindungi oleh **SummaryOutputGuardrail** dan **Fallback Deterministik**.

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

## Arsitektur Pipeline Analisis Stok & Integrasi Gemini

```
[ Request JSON ] ──► [ Validasi Pydantic (Kalender & Angka Finite) ]
                              │
                              ▼
        [ Deterministik Stock Evaluator (core.rules) ]
        - Menghitung status: CRITICAL, WARNING, SAFE
        - Menghitung status_counts: total, critical, warning, safe
                              │
                              ▼
                 [ SummaryPromptBuilder ]
        - System Prompt: Aturan ketat & pembatas peran
        - User Prompt: Isolasi data mentah tidak tepercaya (<inventory_data>)
                              │
                              ▼
             [ Factory Provider LLM Selection ]
             ├── LLM_PROVIDER="gemini" (Async Google Gen AI SDK)
             └── LLM_PROVIDER="mock"   (MockSummaryLLMService)
                              │
                              ▼
                 [ SummaryOutputGuardrail ]
        - Memeriksa validitas skema JSON (LLMSummaryOutput)
        - Memeriksa keabsahan referensi produk (target_item_ref)
        - Memeriksa konsistensi tindakan (RESTOCK_REVIEW, MONITOR, NO_ACTION)
        - Mendeteksi klaim nominal finansial & prediksi waktu spekulatif
                 │                             │
            [ Lolos ]                     [ Gagal / Error / Timeout ]
                 │                             │
                 ▼                             ▼
       [ Format AI Valid ]          [ Fallback ke Ringkasan ]
                                    [ Deterministik Template]
                 │                             │
                 └──────────────┬──────────────┘
                                ▼
                   [ Response JSON Standar ]
```

---

## Konfigurasi Google Gemini API

### 1. Variabel Lingkungan (`.env`)
Salin template konfigurasi dari `.env.example` ke `.env`:
```ini
# Provider: 'mock' (default) atau 'gemini'
LLM_PROVIDER=gemini

# Kunci API Google AI Studio
GEMINI_API_KEY=AIzaSy...KunciRahasiaAnda...

# Model Gemini aktif (dapat dikonfigurasi secara dinamis)
GEMINI_MODEL_NAME=gemini-2.5-flash

# Batas waktu timeout permintaan API (dalam detik)
GEMINI_TIMEOUT_SECONDS=10.0
```

### 2. Model Gemini Aktif yang Direkomendasikan
* **`gemini-2.5-flash`** (Default): Model multimodal generasi terbaru dengan kecepatan tinggi, efisiensi biaya, dan penalaran faktual yang tajam.
* **`gemini-2.0-flash`**: Alternatif model flash generasi 2.0 yang stabil.

### 3. Cara Memeriksa Model yang Tersedia Secara Programatik
Untuk melihat daftar model Gemini yang aktif dan didukung oleh API key Anda, jalankan skrip Python berikut:
```python
from google import genai

client = genai.Client(api_key="ISI_API_KEY_ANDA")
print("Daftar Model Gemini yang Tersedia:")
for model in client.models.list():
    if "gemini" in model.name.lower():
        print(f"- {model.name}")
```

### 4. Transparansi Metadata Respon
* **Jika respon berasal dari Gemini**:
  `meta.provider = "gemini-2.5-flash"`, `meta.fallback_applied = false`, `meta.guardrail_status = "passed"`
* **Jika respon berasal dari Mock**:
  `meta.provider = "mock"`, `meta.fallback_applied = false`, `meta.guardrail_status = "passed"`
* **Jika terjadi kegagalan (Timeout, Quota 429, atau Pelanggaran Guardrail)**:
  `meta.fallback_applied = true`, `meta.guardrail_status = "fallback_triggered: <alasan atau error>"`

---

## Struktur Direktori

```text
ai/genai/
├── requirements.txt             # Dependensi modul AI Assistant (termasuk google-genai)
├── .env.example                 # Template environment variables
├── data/
│   └── synthetic_inventory.json # Data sintetis ilustratif (bukan data riil)
├── src/
│   ├── main.py                  # Entrypoint aplikasi FastAPI
│   ├── core/
│   │   ├── config.py            # Pengaturan aplikasi, timeout, & path resolver
│   │   ├── rules.py             # Definisi aturan SAFE, WARNING, CRITICAL
│   │   ├── prompt_builder.py    # Builder prompt dengan isolasi data tidak tepercaya
│   │   └── guardrails.py        # Validasi output terstruktur & deteksi halusinasi
│   ├── schemas/
│   │   ├── chat.py              # DTO Request & Response interaksi chat
│   │   ├── inventory.py         # DTO data barang & transaksi
│   │   └── summary.py           # DTO Request & Response Daily Stock Summary
│   ├── repositories/
│   │   ├── base.py              # Abstract Base Inventory Repository
│   │   └── mock_inventory.py    # Repository pembaca JSON lokal
│   ├── services/
│   │   ├── llm_base.py          # Abstract Base LLM Service (Chat)
│   │   ├── mock_llm.py          # Generator respons mock chat
│   │   ├── assistant_service.py # Orchestrator chat assistant
│   │   ├── summary_llm.py       # Mock LLM terstruktur untuk ringkasan
│   │   ├── gemini_summary_llm.py# Adapter resmi Google Gen AI SDK (Async)
│   │   └── summary_service.py   # Pipeline ringkasan stok harian & fallback
│   └── api/
│       └── v1/
│           ├── router.py        # Agregator router API v1
│           └── endpoints/
│               ├── health.py    # GET /api/v1/health
│               ├── chat.py      # POST /api/v1/assistant/chat
│               └── summary.py   # POST /api/v1/summary/daily (Factory Provider)
└── tests/
    ├── conftest.py                       # Fixture pytest & path import
    ├── test_stock_rules.py               # Unit test aturan stok & minimum_stock = 0
    ├── test_mock_inventory.py            # Unit test repository & dataset sintetis
    ├── test_mock_llm.py                  # Unit test logika respons mock chat & provider
    ├── test_endpoints.py                 # Integration test endpoint HTTP v1
    ├── test_daily_summary.py             # Unit & integration test Daily Stock Summary
    ├── test_prompt_builder.py            # Unit test isolasi prompt injection & builder
    ├── test_guardrails.py                # Unit test validasi skema, referensi & halusinasi
    ├── test_daily_summary_guardrails.py  # Integration test guardrails & alur fallback
    └── test_gemini_integration.py        # Unit & integration test Gemini adapter (Mocked)
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

Jalankan seluruh test suite menggunakan pytest di dalam virtual environment:
```bash
# Menjalankan seluruh pengujian (tanpa kuota/koneksi API sungguhan):
pytest tests/ -v

# Menjalankan pengujian integrasi adapter Gemini secara spesifik:
pytest tests/test_gemini_integration.py -v
```
Seluruh pengujian dijalankan menggunakan teknik *mock client* terisolasi, sehingga tidak memanggil API Gemini sungguhan dan tidak membutuhkan kuota berbayar.
