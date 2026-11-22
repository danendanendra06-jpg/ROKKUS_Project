# ROKKUS AI Inventory Assistant (GenAI Module)

Modul layanan Generative AI untuk aplikasi **ROKKUS Mardani Raya** (Pengelolaan dan Pemantauan Stok Harian Terintegrasi).

Modul ini bertugas menganalisis stok harian toko, mengklasifikasikan ketersediaan barang secara konsisten dengan standar Data Science, dan menghasilkan narasi ringkasan eksekutif serta rekomendasi tindakan operasional menggunakan integrasi **Google Gen AI SDK resmi (`google-genai`)** atau **Fallback Deterministik** jika layanan AI eksternal tidak tersedia.

---

## 1. Aturan Konsisten Status Stok (DS Aligned)

Klasifikasi status ketersediaan barang dihitung secara otomatis dan absolut berdasarkan aturan pada `src/core/rules.py` yang diselaraskan 100% dengan dataset tim Data Science:

| Status | Formula Kondisi | Makna Operasional UMKM ROKKUS |
| :--- | :--- | :--- |
| **`EMPTY`** | `current_stock == 0` | Stok habis total. Memerlukan **restock darurat hari ini** agar operasional tidak terhenti. |
| **`LOW`** | `1 <= current_stock <= 5` | Stok menipis. Memerlukan **pemantauan ketat** dan penjadwalan pemesanan ulang ke supplier. |
| **`SAFE`** | `current_stock > 5` | Stok aman melampaui batas ambang risiko (stok > 5 unit). Kondisi memadai untuk operasional harian. |

> **Catatan Kompatibilitas `minimum_stock`**:
> Field `minimum_stock` tetap dipertahankan pada DTO request (`DailyStockItemInput`) untuk menjaga kompatibilitas kontrak dengan backend, namun evaluasi klasifikasi status stok GenAI kini mengacu secara absolut pada ambang batas di atas sesuai standar tim Data Science.

---

## 2. Arsitektur Pipeline Analisis Stok & Integrasi Gemini

```
[ Request JSON Backend ] ──► [ Validasi Pydantic (Format Tanggal & Nilai Finite) ]
                                            │
                                            ▼
                          [ Deterministik Stock Evaluator (core.rules) ]
                          - Evaluasi status: EMPTY, LOW, SAFE
                          - Hitung status_counts: total_items, empty, low, safe
                                            │
                                            ▼
                               [ SummaryPromptBuilder ]
                          - System Prompt: Aturan peran, batas konteks, format JSON ketat
                          - User Prompt: Isolasi data stok mentah dalam tag <inventory_data>
                                            │
                                            ▼
                               [ Factory Provider LLM Selection ]
                               ├── LLM_PROVIDER="gemini" (Async Google Gen AI SDK)
                               └── LLM_PROVIDER="mock"   (MockSummaryLLMService)
                                            │
                                            ▼
                                [ SummaryOutputGuardrail ]
                          - Memeriksa kelengkapan & validitas skema respons
                          - Memeriksa keabsahan produk (mencegah halusinasi nama produk)
                          - Memeriksa konsistensi tindakan (RESTOCK_REVIEW, MONITOR, NO_ACTION)
                          - Memblokir klaim nominal finansial & janji waktu spekulatif
                                    │                             │
                               [ Lolos ]                     [ Gagal / Error / Timeout / 503 ]
                                    │                             │
                                    ▼                             ▼
                          [ Format AI Terstruktur ]     [ Fallback ke Ringkasan Deterministik ]
                                    │                             │
                                    └──────────────┬──────────────┘
                                                   ▼
                                [ DailyStockSummaryResponse JSON ]
```

---

## 3. Instalasi dan Setup Environment

### Prasyarat
- Python 3.10+ (Direkomendasikan Python 3.12)
- Koneksi internet untuk unduh dependensi

### Langkah Instalasi
```powershell
# 1. Masuk ke direktori modul GenAI
cd ai/genai

# 2. Buat virtual environment
python -m venv .venv

# 3. Aktivasi virtual environment
# Windows (PowerShell):
.\.venv\Scripts\Activate.ps1
# Linux / macOS:
# source .venv/bin/activate

# 4. Instal dependensi
pip install -r requirements.txt
```

### Konfigurasi File Lingkungan (`.env`)
Salin file `.env.example` menjadi `.env` di dalam `ai/genai/`:
```ini
# Identitas Aplikasi
APP_NAME="ROKKUS AI Inventory Assistant"
APP_VERSION="1.0.0"
ENVIRONMENT="development"

# Provider LLM: 'mock' (default) atau 'gemini'
LLM_PROVIDER=mock

# Google Gemini API Configuration
GEMINI_API_KEY=""
GEMINI_MODEL_NAME="gemini-2.5-flash"
GEMINI_TIMEOUT_SECONDS=10.0

# Path dataset inventaris lokal (opsional)
INVENTORY_DATA_PATH="data/synthetic_inventory.json"
```

> **Keamanan Kredensial**:
> File `.env` bersifat lokal dan telah diabaikan oleh `.gitignore`. Jangan pernah melakukan commit file `.env` atau mengekspos API key ke repositori publik.

---

## 4. Menjalankan Server FastAPI

Jalankan server aplikasi menggunakan Uvicorn:
```powershell
uvicorn src.main:app --host 127.0.0.1 --port 8000 --reload
```
Dokumentasi interaktif dapat diakses melalui browser:
- **Swagger UI**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **ReDoc**: [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)
- **Health Check**: [http://127.0.0.1:8000/api/v1/health](http://127.0.0.1:8000/api/v1/health)

---

## 5. Dokumentasi Endpoint & Kontrak Backend

### POST `/api/v1/summary/daily`
Endpoint utama untuk memproses data stok harian dan menyusun ringkasan eksekutif.

#### Contoh Request Payload (dari Backend):
```json
{
  "date": "2026-11-22",
  "store_name": "ROKKUS Mardani Raya",
  "items": [
    {
      "name": "Lotus Biscoff",
      "current_stock": 0.0,
      "minimum_stock": 5.0,
      "unit": "porsi",
      "category": "Roti Manis"
    },
    {
      "name": "Keju Slice",
      "current_stock": 3.0,
      "minimum_stock": 5.0,
      "unit": "slice",
      "category": "Tambahan"
    },
    {
      "name": "Roti Gandum",
      "current_stock": 15.0,
      "minimum_stock": 5.0,
      "unit": "buah",
      "category": "Bahan Baku"
    }
  ]
}
```

#### Contoh Response Sukses (HTTP 200):
```json
{
  "status": "success",
  "data": {
    "date": "2026-11-22",
    "store_name": "ROKKUS Mardani Raya",
    "summary": "Ringkasan Stok Harian (2026-11-22) - ROKKUS Mardani Raya:\nTotal 3 barang dipantau. Ditemukan 1 barang habis (EMPTY) dan 1 barang menipis (LOW).\nBarang habis: Lotus Biscoff (0 porsi).\nBarang menipis: Keju Slice (3 slice).\nSebanyak 1 barang dalam kondisi aman (SAFE).\nPrioritaskan restock untuk barang habis agar operasional lancar.",
    "status_counts": {
      "empty": 1,
      "low": 1,
      "safe": 1,
      "total_items": 3
    },
    "items": [
      {
        "id": null,
        "item_ref": null,
        "name": "Lotus Biscoff",
        "category": "Roti Manis",
        "current_stock": 0.0,
        "minimum_stock": 5.0,
        "unit": "porsi",
        "status": "EMPTY",
        "status_description": "Stok habis (current_stock == 0). Perlu restock segera."
      },
      {
        "id": null,
        "item_ref": null,
        "name": "Keju Slice",
        "category": "Tambahan",
        "current_stock": 3.0,
        "minimum_stock": 5.0,
        "unit": "slice",
        "status": "LOW",
        "status_description": "Stok menipis (1 <= current_stock <= 5). Perlu pemantauan."
      },
      {
        "id": null,
        "item_ref": null,
        "name": "Roti Gandum",
        "category": "Bahan Baku",
        "current_stock": 15.0,
        "minimum_stock": 5.0,
        "unit": "buah",
        "status": "SAFE",
        "status_description": "Stok aman (current_stock > 5)."
      }
    ],
    "suggested_actions": [
      "Lakukan pemesanan ulang (restock) darurat hari ini untuk: Lotus Biscoff (stok 0 porsi).",
      "Pantau ketersediaan dan jadwalkan restock segera untuk: Keju Slice (sisa 3 slice)."
    ],
    "meta": {
      "provider": "mock",
      "requested_provider": "mock",
      "execution_provider": "mock",
      "is_synthetic": true,
      "source": "synthetic_input",
      "disclaimer": "Pemberitahuan: Ringkasan stok harian dihasilkan oleh Mock Service untuk kebutuhan pengujian lokal ROKKUS.",
      "generated_at": "2026-11-22T08:30:00.000000+00:00",
      "fallback_applied": false,
      "guardrail_status": "passed"
    }
  }
}
```

---

## 6. Transparansi Metadata Respon & Engine Fallback

Metadata pada objek `data.meta` dirancang untuk auditabilitas penuh dan integritas sistem produksi:

| Field Metadata | Tipe | Penjelasan |
| :--- | :--- | :--- |
| `requested_provider` | `str` | Provider yang awalnya diminta sistem (`"gemini-2.5-flash"` atau `"mock"`). |
| `execution_provider` | `str` | Provider yang nyata mengeksekusi teks ringkasan (`"gemini-2.5-flash"`, `"mock"`, atau `"deterministic_fallback"`). |
| `provider` | `str` | Alias backward-compatible yang nilainya selalu disinkronkan dengan `execution_provider`. |
| `fallback_applied` | `bool` | Bernilai `true` jika terjadi fallback deterministik akibat timeout, kuota 429, error 503, atau pelanggaran guardrail. |
| `guardrail_status` | `str` | Status evaluasi guardrail (`"passed"` atau deskripsi pemicu fallback seperti `"fallback_triggered: 503 UNAVAILABLE"`). |
| `disclaimer` | `str` | Narasi dinamis yang transparan menjelaskan sumber data dan sifat pembentukan ringkasan. |

---

## 7. Adapter Dataset Data Science (`DSDatasetAdapter`)

Adapter read-only pada `src/adapters/ds_dataset_adapter.py` membaca dataset sintetis tim Data Science langsung dari path disk atau fallback git tanpa mengubah atau menyalin file DS:
- **Lokasi Dataset Target**: `data-science/data/processed/dataset_stok_rokkus_final.csv`.
- **Cakupan Data**: 29 produk menu ROKKUS (kondisi awal per 1 September 2026).
- **Hasil Pemetaan Status**:
  - **EMPTY (5 produk)**: Nutella Keju, Srikaya, Strawberry, Tiramisu, Telur Beef Sosis.
  - **LOW (8 produk)**: Keju, Telur Mayo, Telur Sosis Mayo, Telur Beef, Double Beef, Keju Slice, Keju Parut, Telur.
  - **SAFE (16 produk)**: Lotus Biscoff, Coklat Keju, Coklat Kacang, Silverqueen Keju, Ovomaltine Keju, Coklat Crunchy, Blueberry, Greentea, Kacang, Nutella, Silverqueen, Ovomaltine, Sosis Mayo, Beef Mayo, Beef Sosis Mayo, Selai Lain.
- Adapter menyisipkan metadata `is_synthetic: true` dan peringatan bahwa data bersifat prototipe simulasi.

---

## 8. Simulasi Integrasi Machine Learning & Pemisahan Semantik

Modul `src/adapters/ml_integration_adapter.py` dan `src/schemas/ml_integration.py` menghubungkan GenAI dengan kontrak model ML Husain (`POST /ml/predict-status`):

### 11 Fitur Input ML Wajib
Model ML memerlukan 11 fitur numerik dan kategorik per item:
1. `stok_saat_ini` (float $\ge 0$)
2. `batas_minimum` (float $\ge 0$)
3. `barang_masuk` (float $\ge 0$)
4. `barang_keluar` (float $\ge 0$)
5. `avg_keluar_7h` (float $\ge 0$) - *Rolling mean 7 hari*
6. `days_of_cover` (float $\ge 0$) - *Stok cukup untuk N hari*
7. `rasio_stok` (float $\ge 0$) - *stok_saat_ini / batas_minimum*
8. `total_masuk_7h` (float $\ge 0$) - *Rolling sum 7 hari*
9. `total_keluar_7h` (float $\ge 0$) - *Rolling sum 7 hari*
10. `kategori` (str non-kosong: `"roti_kukus"` / `"roti_bakar"`)
11. `rasa` (str non-kosong)

### Pemisahan Semantik (Domain Separation)
- **Status Stok Faktual (DS / GenAI)**: `EMPTY`, `LOW`, `SAFE` (fakta stok akhir hari ini).
- **Prediksi Risiko Stok (ML)**: `habis`, `menipis`, `aman` (estimasi kemungkinan risiko masa depan).
- **Pengayaan Non-Destruktif**: Hasil ML disematkan ke `suggested_actions` dengan tag `[ML_RISK_PREDICTION]` tanpa mengubah agregasi `status_counts` faktual.

### Batasan Nyata & Kejujuran Data
- Dataset DS saat ini baru mencakup 1 snapshot harian, sehingga **tidak memiliki histori 7 hari**.
- Modul GenAI **tidak memalsukan data histori 7 hari**. Jika histori tidak lengkap, sistem menolak pembuatan fitur ML tiruan secara eksplisit.
- **Resilience**: Jika service ML mengalami 503 atau belum aktif, GenAI tetap memberikan respons ringkasan faktual secara stabil (*graceful degradation*).

---

## 9. Hasil Pengujian Aktual & Keterbatasan Live Gemini API

Pengujian otomatis dijalankan secara berkala menggunakan pytest:
```powershell
pytest ai/genai/tests/ -v
```
**Status Pengujian Terkini**:
- **Total Tests**: **86 passed, 0 failed** (100% kelulusan).
- **Cakupan Pengujian**:
  - `test_stock_rules.py`: Evaluasi status EMPTY, LOW, SAFE (14 tests).
  - `test_ds_adapter.py`: Validasi adapter dataset DS (7 tests).
  - `test_backend_contract.py`: Validasi kontrak payload backend & HTTP 422 (4 tests).
  - `test_gemini_integration.py`: Mock timeout, 429, dan 503 UNAVAILABLE (10 tests).
  - `test_guardrails.py` & `test_daily_summary_guardrails.py`: Keamanan prompt & deteksi halusinasi (14 tests).
  - `test_ml_integration.py`: Kontrak 11 fitur ML & resilience fallback (9 tests).
  - `test_endpoints.py`, `test_daily_summary.py`, `test_mock_inventory.py`, `test_mock_llm.py`, `test_prompt_builder.py` (28 tests).

### Keterbatasan Live Gemini API
Pada pengujian live request menggunakan `google-genai` SDK dan model `gemini-2.5-flash`, server Google AI Studio sempat mengalami kendala kapasitas (`503 UNAVAILABLE: The model is overloaded`). 
Arsitektur GenAI ROKKUS telah dilengkapi dengan engine fallback deterministik yang secara otomatis mengambil alih proses sehingga aplikasi tidak pernah mengalami crash, sembari menjaga akurasi data inventaris UMKM.
