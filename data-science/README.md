# Data Science - ROKKUS Mardani Raya

## 1. Deskripsi Project

Bagian Data Science mendukung pengembangan aplikasi pengelolaan dan pemantauan stok harian terintegrasi pada UMKM ROKKUS Mardani Raya. Pekerjaan mencakup penyusunan data produk, simulasi pergerakan stok, pengolahan data, Exploratory Data Analysis (EDA), klasifikasi status stok berbasis aturan, visualisasi, dan pengujian fungsional.

## 2. Tujuan

- Menyusun master data produk berdasarkan daftar menu yang diberikan.
- Menyiapkan data sintetis stok awal dan transaksi stok.
- Menghitung stok akhir produk dari stok awal, stok masuk, dan stok keluar.
- Menganalisis distribusi stok dan pergerakan stok.
- Mengelompokkan status stok menjadi Safe, Low, dan Empty menggunakan aturan simulasi.
- Menyiapkan ringkasan dan file pendukung integrasi aplikasi.

## 3. Teknologi

- Python dan Google Colab
- Pandas dan NumPy
- Matplotlib

## 4. Struktur Folder

```text
ROKKUS_Project/
└── data-science/
    ├── notebooks/
    │   ├── ROKKUS_Data_Preparation.ipynb
    │   └── ROKKUS_Data_Science.ipynb
    ├── data/
    │   ├── raw/
    │   │   ├── master_produk_rokkus.csv
    │   │   ├── stok_awal.csv
    │   │   └── transaksi_stok.csv
    │   └── processed/
    │       ├── dataset_stok_rokkus_final.csv
    │       ├── hasil_klasifikasi_stok_rokkus.csv
    │       └── ringkasan_stok_rokkus.csv
    ├── outputs/
    │   ├── dashboard_summary_rokkus.csv
    │   ├── grafik_distribusi_status.png
    │   ├── grafik_stok_masuk_keluar.png
    │   ├── grafik_stok_per_kategori.png
    │   └── hasil_pengujian_fungsional.csv
    └── README.md
```

## 5. Notebook

- `ROKKUS_Data_Preparation.ipynb`: penyusunan dan pengolahan dataset sintetis yang disiapkan untuk skenario project ROKKUS.
- `ROKKUS_Data_Science.ipynb`: eksplorasi dataset inventori publik untuk latihan dan referensi analisis. Dataset publik ini bukan data operasional ROKKUS.

## 6. Dataset dan Batasan

Master produk disusun dari daftar menu yang dibagikan untuk project. Data stok awal dan transaksi dibuat secara sintetis karena data operasional atau transaksi aktual tidak tersedia untuk pengolahan ini.

Dataset simulasi menggunakan periode 1–30 September 2026 dengan 300 transaksi buatan. Angka-angka tersebut tidak boleh ditafsirkan sebagai catatan atau pola penjualan aktual UMKM.

Cakupan stok pada simulasi ini adalah produk jadi. Data bahan baku tidak dimodelkan.

## 7. Tahapan Pengerjaan

1. Penyusunan master data produk.
2. Pembuatan dataset sintetis stok awal dan transaksi.
3. Data understanding dan pemeriksaan kualitas data.
4. Data preprocessing dan perhitungan stok.
5. Exploratory Data Analysis (EDA).
6. Klasifikasi status stok dengan pendekatan rule-based.
7. Evaluasi hasil klasifikasi.
8. Pembuatan visualisasi dan ringkasan dashboard.
9. Pengujian fungsional.

## 8. Aturan Klasifikasi Simulasi

| Status | Aturan |
|---|---|
| Empty | Stok akhir sama dengan 0 |
| Low | Stok akhir 1 sampai 5 |
| Safe | Stok akhir lebih dari 5 |

Batas 5 unit merupakan asumsi untuk simulasi, bukan batas minimum resmi dari UMKM. Aturan perlu dikonfirmasi dengan pihak UMKM sebelum digunakan sebagai aturan operasional.

Klasifikasi saat ini berbasis aturan (rule-based), bukan model machine learning atau prediksi permintaan.

## 9. Ringkasan Hasil Dataset Sintetis

Berdasarkan hasil pengolahan dan validasi dataset sintetis terbaru:

- Jumlah produk: 29
- Jumlah transaksi: 300
- Total stok awal: 608
- Total stok masuk: 620
- Total stok keluar: 896
- Total stok akhir: 332
- Status Safe: 16 produk
- Status Low: 8 produk
- Status Empty: 5 produk
- Jumlah kejadian stok negatif selama simulasi transaksi: 0

Rumus perhitungan:

`stok_akhir = stok_awal + total_masuk - total_keluar`

Perhitungan total:

`608 + 620 - 896 = 332`

Hasil ini hanya menggambarkan dataset sintetis dan tidak merepresentasikan kondisi persediaan aktual UMKM ROKKUS.

## 10. Pengujian Fungsional

Pengujian fungsional dilakukan menggunakan lima pemeriksaan otomatis:

1. Memastikan jumlah produk sesuai, yaitu 29 produk.
2. Memastikan tidak terdapat stok akhir negatif.
3. Memastikan perhitungan stok akhir sesuai dengan rumus stok.
4. Memastikan seluruh produk memiliki klasifikasi status stok.
5. Memastikan nilai total stok pada dashboard sesuai dengan ringkasan stok.

Berdasarkan hasil pengujian terakhir yang dijalankan pada dataset sintetis, diperoleh hasil sebagai berikut:

- PASS: 5
- FAIL: 0

Pengujian perlu dijalankan kembali apabila dataset atau aturan klasifikasi diubah.

## 11. Output

Folder `outputs/` berisi:

- `dashboard_summary_rokkus.csv`: ringkasan jumlah produk, stok akhir, stok masuk, stok keluar, dan distribusi status stok.
- `grafik_stok_per_kategori.png`: visualisasi total stok akhir berdasarkan kategori.
- `grafik_stok_masuk_keluar.png`: visualisasi perbandingan stok masuk dan stok keluar berdasarkan kategori.
- `grafik_distribusi_status.png`: visualisasi distribusi status stok produk.
- `hasil_pengujian_fungsional.csv`: hasil pengujian fungsional dataset.

Seluruh output merupakan hasil pengolahan dataset sintetis dan disiapkan sebagai bahan pendukung pengembangan serta diskusi integrasi dengan tim Full-stack dan Gen AI.

---

**Project:** Pengembangan Aplikasi Pengelolaan dan Pemantauan Stok Harian Terintegrasi pada UMKM ROKKUS Mardani Raya

**Divisi:** Data Science
