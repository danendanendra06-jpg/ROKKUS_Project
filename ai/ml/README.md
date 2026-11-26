# ROKKUS ML – Klasifikasi Status Stok Harian

**Capstone Asah 2026 | Tim A26-CS159**  
Use Case: Aplikasi pengelolaan dan pemantauan stok harian UMKM ROKKUS Mardani Raya (roti kukus dan roti bakar)

---

## Deskripsi

Modul ini menyediakan layanan pemantauan dan klasifikasi status stok per SKU produk ROKKUS menjadi tiga status operasional:
- **`habis`** : `stok_saat_ini <= 0`
- **`menipis`**: `stok_saat_ini > 0` dan `stok_saat_ini <= batas_minimum`
- **`aman`**   : `stok_saat_ini > batas_minimum`

### Catatan Arsitektur: Rule-Based vs Machine Learning
1. **Klasifikasi Status Stok Aktual (Rule-Based - Disarankan untuk Operasional):**
   Status stok fisik harian bersifat deterministik sesuai kesepakatan bisnis di atas. Evaluasi status aktual dan penanda stok menipis dijalankan menggunakan fungsi `classify_stock_status()` dan `flag_stok_menipis()` di `src/predict.py` serta endpoint `POST /ml/status`. Pendekatan ini instan, akurat 100%, dan **tidak memerlukan file model `.joblib`**.
2. **Inferensi Model Machine Learning (`POST /ml/predict-status` - Eksperimen/Legacy):**
   Model Random Forest/Gradient Boosting yang telah dilatih tersimpan di `models/best_model.joblib`. Endpoint ini tetap dipertahankan untuk backward-compatibility eksperimen komparasi model. Prediksi stok masa depan ditunda ke fase berikutnya.

---

## Formula Klasifikasi Status Stok Aktual

$$\text{Status}(i) = \begin{cases} 
\mathbf{habis}, & \text{jika } \text{stok\_saat\_ini} \le 0 \\
\mathbf{menipis}, & \text{jika } \text{stok\_saat\_ini} > 0 \;\land\; \text{stok\_saat\_ini} \le \text{batas\_minimum} \\
\mathbf{aman}, & \text{jika } \text{stok\_saat\_ini} > \text{batas\_minimum}
\end{cases}$$

*Catatan: Pada tahap ini, metrik `days_of_cover` tidak mengubah status aktual, namun tetap dapat disertakan sebagai indikator peringatan tambahan.*

---

## Struktur Direktori

```
ai/ml/
├── README.md                    ← Dokumentasi ini
├── requirements.txt             ← Dependencies Python
├── pytest.ini                   ← Konfigurasi pytest
├── conftest.py                  ← Setup path untuk pytest
│
├── configs/
│   └── config.yaml              ← Semua konfigurasi (path, kolom, label, model)
│
├── sample_data/                 ← Data sintetis (placeholder, BUKAN data asli)
│   └── stok_harian.csv
│
├── src/
│   ├── make_dummy_data.py       ← Generator data sintetis
│   ├── preprocessing.py         ← Load, cleaning, feature engineering, split
│   ├── train.py                 ← Training & pemilihan model terbaik
│   ├── evaluate.py              ← Metrik & laporan perbandingan
│   ├── predict.py               ← Inferensi & flag_stok_menipis
│   └── api.py                   ← FastAPI router + standalone app
│
├── models/
│   ├── best_model.joblib        ← Model terbaik (hasil train.py)
│   └── metadata.json            ← Versi, fitur, metrik, tanggal latih
│
├── reports/
│   ├── model_comparison.csv     ← Tabel metrik semua model
│   ├── model_comparison.md      ← Laporan lengkap + alasan pemilihan + keterbatasan
│   └── figures/
│       ├── cm_LogisticRegression.png
│       ├── cm_RandomForest.png
│       ├── cm_GradientBoosting.png
│       └── metric_comparison.png
│
└── tests/
    ├── test_preprocessing.py
    ├── test_predict.py
    └── test_api.py
```

---

## Setup & Instalasi

### Prasyarat
- Python ≥ 3.10; Python 3.14.3 adalah versi yang digunakan untuk environment lokal ini
- Akses internet untuk download packages

### 1. Buat Virtual Environment

```powershell
# Dari root repository, buat environment lokal di ai\ml\venv
py -3.14 -m venv ai\ml\venv

# Bootstrap pip jika belum tersedia, lalu pasang dependencies di environment ini
.\ai\ml\venv\Scripts\python.exe -m ensurepip --upgrade
.\ai\ml\venv\Scripts\python.exe -m pip install --upgrade pip
.\ai\ml\venv\Scripts\python.exe -m pip install -r ai\ml\requirements.txt
.\ai\ml\venv\Scripts\python.exe -m pip check
```

Jika perintah `py -3.14` tidak tersedia, gunakan interpreter Python 3.14 yang terpasang:

```powershell
& "C:\Program Files\Python314\python.exe" -m venv ai\ml\venv
```

Environment yang sudah ada tidak perlu dibuat ulang. Jalankan perintah `ensurepip`, instalasi dependencies, dan `pip check` di atas untuk menyiapkannya.

Di VS Code, pilih interpreter `ai\ml\venv\Scripts\python.exe` melalui **Python: Select Interpreter**. Jika PowerShell menghalangi aktivasi environment, gunakan jalur interpreter lengkap seperti pada perintah di atas; aktivasi tidak wajib.

Untuk Linux/macOS, buat environment dengan `python3 -m venv ai/ml/venv`, lalu gunakan `ai/ml/venv/bin/python -m ensurepip --upgrade` dan `ai/ml/venv/bin/python -m pip install -r ai/ml/requirements.txt`.

---

## Workflow Lengkap

### Langkah 1: Generate Data Sintetis (jika dataset belum ada)

```powershell
python src/make_dummy_data.py
# Output: sample_data/stok_harian.csv
```

> ⚠️ Data ini **sintetis** (placeholder). Ganti dengan data asli setelah tersedia.  
> Lihat bagian **Swap ke Data Asli** di bawah.

### Langkah 2: Training & Evaluasi

```powershell
python src/train.py
# Melatih 3 model, memilih terbaik, menyimpan ke models/

python src/train.py --tune
# Aktifkan GridSearchCV (lebih lambat, opsional)
```

Output training:
- `models/best_model.joblib`
- `models/metadata.json`
- `reports/model_comparison.csv`
- `reports/model_comparison.md`
- `reports/figures/*.png`

### Langkah 3: Inferensi via Python

```python
import sys
sys.path.insert(0, "src")

from predict import predict_status, flag_stok_menipis

# Prediksi status stok
hasil = predict_status({
    "stok_saat_ini":   5.0,
    "batas_minimum":  15.0,
    "barang_masuk":   20.0,
    "barang_keluar":  30.0,
    "avg_keluar_7h":  28.0,
    "days_of_cover":   0.18,
    "rasio_stok":      0.33,
    "total_masuk_7h": 140.0,
    "total_keluar_7h": 196.0,
    "kategori":        "roti_kukus",
    "rasa":            "coklat",
})
print(hasil)
# → {"status": "menipis", "probabilitas": {"aman": 0.02, "menipis": 0.95, "habis": 0.03}, "versi_model": "1.0.0"}

# Rule-based flag (tidak butuh model)
flag = flag_stok_menipis(stok_saat_ini=5.0, batas_minimum=15.0, days_of_cover=0.18)
print(flag)
# → {"is_menipis": True, "is_habis": False, "alasan": "...", "saran": "..."}
```

### Langkah 4: Jalankan API

```powershell
# Standalone (port 8001)
uvicorn src.api:app --reload --port 8001

# Akses docs
# http://localhost:8001/ml/docs
```

#### A. Endpoint Utama: Klasifikasi Status Stok Aktual (`POST /ml/status`) — Rule-Based
Endpoint ini **tidak membutuhkan file model `.joblib`** dan menerima payload minimal.

**Request:**
```bash
curl -X POST http://localhost:8001/ml/status \
  -H "Content-Type: application/json" \
  -d '{
    "items": [
      {
        "stok_saat_ini": 3.0,
        "batas_minimum": 5.0,
        "id_barang": "PR001",
        "nama_barang": "Lotus Biscoff"
      }
    ]
  }'
```

**Response:**
```json
{
  "total_items": 1,
  "hasil": [
    {
      "id_barang": "PR001",
      "nama_barang": "Lotus Biscoff",
      "status": "menipis",
      "is_menipis": true,
      "is_habis": false,
      "alasan": "Stok (3.00 unit) berada di bawah atau sama dengan batas minimum (5.00 unit).",
      "saran": "Pertimbangkan resupply segera untuk mencegah stok habis.",
      "metode": "rule_based"
    }
  ]
}
```

#### B. Endpoint Inferensi Model ML (`POST /ml/predict-status`) — Legacy/Model
Memerlukan file model `models/best_model.joblib` dan 11 fitur input lengkap.

**Request:**
```bash
curl -X POST http://localhost:8001/ml/predict-status \
  -H "Content-Type: application/json" \
  -d '{
    "items": [{
      "stok_saat_ini": 5.0,
      "batas_minimum": 15.0,
      "barang_masuk": 20.0,
      "barang_keluar": 30.0,
      "avg_keluar_7h": 28.0,
      "days_of_cover": 0.18,
      "rasio_stok": 0.33,
      "total_masuk_7h": 140.0,
      "total_keluar_7h": 196.0,
      "kategori": "roti_kukus",
      "rasa": "coklat"
    }]
  }'
```

**Contoh response:**
```json
{
  "total_items": 1,
  "prediksi": [{
    "status": "menipis",
    "probabilitas": {"aman": 0.02, "menipis": 0.95, "habis": 0.03},
    "versi_model": "1.0.0"
  }]
}
```

### Langkah 5: Jalankan Tests

```powershell
# Semua test
pytest

# Test spesifik
pytest tests/test_preprocessing.py -v
pytest tests/test_predict.py -v
pytest tests/test_api.py -v

# Test termasuk yang butuh model (setelah train.py)
pytest -v --no-header
```

---

## Swap ke Data Asli

Ketika dataset asli dari tim data tersedia:

1. **Letakkan CSV** di `data/` (atau path lain sesuai kesepakatan tim)
2. **Edit `configs/config.yaml`**:
   ```yaml
   data:
     path_data: "../../data/nama_file_asli.csv"  # relatif terhadap ai/ml/
     kolom:
       id_barang:    "ID_Barang"      # sesuaikan dengan nama kolom CSV asli
       nama_barang:  "Nama_Produk"
       # ... dst
   ```
3. **Jalankan ulang training**: `python src/train.py`
4. Tidak perlu mengubah kode preprocessing atau training.

---

## Format Data CSV

| Kolom | Tipe | Keterangan |
|---|---|---|
| `id_barang` | string | ID unik per SKU (mis. "SKU-001") |
| `nama_barang` | string | Nama produk |
| `kategori` | string | "roti_kukus" atau "roti_bakar" |
| `rasa` | string | Varian rasa (mis. "coklat", "keju") |
| `tanggal` | date (YYYY-MM-DD) | Tanggal pencatatan |
| `stok_awal` | int ≥ 0 | Stok awal hari itu |
| `barang_masuk` | int ≥ 0 | Unit masuk (produksi/resupply) |
| `barang_keluar` | int ≥ 0 | Unit terjual/keluar |
| `stok_akhir` | int ≥ 0 | Stok akhir hari itu |
| `batas_minimum` | int ≥ 0 | Ambang stok minimum per SKU |

---

## Fitur Model

| Fitur | Keterangan |
|---|---|
| `stok_saat_ini` | Alias `stok_akhir` – stok sisa hari itu |
| `batas_minimum` | Ambang minimum SKU |
| `barang_masuk` | Jumlah masuk hari itu |
| `barang_keluar` | Jumlah keluar hari itu |
| `avg_keluar_7h` | Rolling mean 7 hari barang_keluar |
| `days_of_cover` | stok_saat_ini / avg_keluar_7h (clipped 30 hari) |
| `rasio_stok` | stok_saat_ini / batas_minimum |
| `total_masuk_7h` | Rolling sum 7 hari barang_masuk |
| `total_keluar_7h` | Rolling sum 7 hari barang_keluar |
| `kategori` | Kategori produk (OrdinalEncoded) |
| `rasa` | Varian rasa (OrdinalEncoded) |

---

## Endpoint API

| Method | Path | Deskripsi |
|---|---|---|
| `GET` | `/ml/health` | Health check, cek model tersedia |
| `POST` | `/ml/predict-status` | Prediksi status stok (batch support) |
| `GET` | `/ml/docs` | Swagger UI interaktif |
| `GET` | `/ml/redoc` | ReDoc dokumentasi |

**Error Codes:**

| Code | Kondisi |
|---|---|
| 200 | Prediksi berhasil |
| 400 | Input tidak valid (nilai negatif, dll.) |
| 422 | Validasi Pydantic gagal (kolom hilang/tipe salah) |
| 503 | Model belum tersedia (jalankan `train.py`) |

---

## Catatan Integrasi

> Karena aturan proyek melarang perubahan di luar `ai/ml/`, berikut adalah langkah yang perlu dilakukan **oleh tim backend** untuk integrasi penuh.

### 1. Daftarkan Router ke Backend FastAPI

Di file router/main backend (mis. `backend/app/main.py`), tambahkan:

```python
import sys
sys.path.insert(0, "/path/to/ai/ml/src")  # atau gunakan path relatif / env var

from api import router as ml_router
app.include_router(ml_router)
```

Atau, jika menggunakan env var:
```python
import os
ml_path = os.getenv("ROKKUS_ML_SRC", "../ai/ml/src")
sys.path.insert(0, ml_path)
```

### 2. Tambahkan ke `.gitignore` Root

Tim yang mengelola `.gitignore` perlu menambahkan:
```
# ROKKUS ML virtual environment
ai/ml/venv/
ai/ml/__pycache__/
ai/ml/src/__pycache__/
ai/ml/tests/__pycache__/
```

### 3. Variabel Environment yang Disarankan

```bash
ROKKUS_ML_CONFIG=ai/ml/configs/config.yaml
ROKKUS_ML_MODEL=ai/ml/models/best_model.joblib
```

### 4. Contoh Docker Integration

```dockerfile
# Tambahkan ke Dockerfile backend (jika monorepo)
COPY ai/ml/requirements.txt /app/ml-requirements.txt
RUN pip install -r /app/ml-requirements.txt
COPY ai/ml/ /app/ml/
ENV ROKKUS_ML_SRC=/app/ml/src
```

---

## Keterbatasan & Catatan Penting

1. **Data Sintetis**: Semua data di `sample_data/` adalah data buatan, bukan data asli ROKKUS. Distribusi stok dan pola musiman mungkin berbeda dari kondisi nyata.

2. **Rule-Based Labeling**: Label `status_stok` dibuat dari aturan deterministic. Model mempelajari kembali aturan tersebut dari fitur turunan. Lihat `reports/model_comparison.md § Keterbatasan`.

3. **Data Leakage**: Fitur `days_of_cover` dan `rasio_stok` berkaitan erat dengan label. Ini disengaja karena relevan secara bisnis, namun menyebabkan akurasi model tinggi secara "artifisial" pada data sintetis.

4. **Split Berbasis Waktu**: Train = 80% data awal, Test = 20% data akhir. Ini lebih konservatif dari random split.

5. **Retraining Wajib**: Lakukan retraining dengan data asli sebelum deployment ke produksi.
