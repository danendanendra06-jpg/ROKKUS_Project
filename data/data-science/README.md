# Data Science - ROKKUS Mardani Raya

## 1. Deskripsi Project

Bagian Data Science mendukung pengembangan aplikasi pengelolaan dan pemantauan stok harian terintegrasi pada UMKM ROKKUS Mardani Raya. Pekerjaan mencakup penyusunan dataset produk jadi dan bahan baku, simulasi pergerakan stok, pengolahan data, Exploratory Data Analysis (EDA), klasifikasi status stok berbasis aturan, visualisasi, dan pengujian fungsional.

## 2. Tujuan

- Menyusun dataset produk jadi dan bahan baku untuk kebutuhan project.
- Menyiapkan data sintetis stok awal dan transaksi stok.
- Menghitung stok akhir berdasarkan stok awal, stok masuk, dan stok keluar.
- Menganalisis distribusi stok dan pergerakan stok.
- Mengelompokkan status stok produk jadi menjadi Safe, Low, dan Empty menggunakan aturan simulasi.
- Melakukan eksplorasi dan visualisasi data untuk mendukung analisis persediaan.
- Menyiapkan dataset hasil pengolahan dan file pendukung integrasi aplikasi.

## 3. Teknologi

- Python dan Google Colab
- Pandas dan NumPy
- Matplotlib

## 4. Struktur Folder

```text
Data-Science/
├── notebooks/
│   ├── ROKKUS_Data_Preparation.ipynb
│   └── ROKKUS_Data_Science.ipynb
├── data/
│   ├── raw/
│   │   ├── master_produk_rokkus.csv
│   │   ├── stok_awal.csv
│   │   ├── transaksi_stok.csv
│   ├── dictionary/
│   │   ├── data_dictionary_dataset_bahan_baku_final.csv
│   │   ├── data_dictionary_produk_jadi.csv
│   │   ├── data_dictionary_stok_rokkus_final.csv
│   │   └── data_dictionary_transaksi_produk.csv
│   └── processed/
│       ├── dataset_bahan_baku_final.csv
│       ├── dataset_produk_jadi_final.csv
│       ├── dataset_stok_rokkus_final.csv
│       ├── hasil_klasifikasi_stok_rokkus.csv
│       └── ringkasan_stok_rokkus.csv
├── outputs/
│   ├── dashboard_summary_rokkus.csv
│   ├── grafik_distribusi_status.png
│   ├── grafik_stok_masuk_keluar.png
│   ├── grafik_stok_per_kategori.png
│   ├── eda_perbandingan_stok_produk.png
│   ├── eda_status_bahan_baku.png
│   ├── eda_status_produk_jadi.png
│   ├── eda_stok_akhir_bahan_baku.png
│   ├── eda_stok_produk_per_kategori.png
│   ├── hasil_pengujian_fungsional.csv
│   └── hasil_pengujian_dataset_final.csv
├── requirements.txt
└── README.md
```


## 5. Notebook

- `ROKKUS_Data_Preparation.ipynb`: penyusunan dan pengolahan dataset sintetis untuk skenario pengelolaan stok produk jadi ROKKUS, termasuk pemeriksaan kualitas data, perhitungan stok, klasifikasi, visualisasi, dan pengujian fungsional.
- `ROKKUS_Data_Science.ipynb`: eksplorasi dan analisis dataset inventori publik sebagai referensi pembelajaran dan pendukung analisis. Dataset publik bukan data operasional ROKKUS.

## 6. Dataset dan Batasan

Project ini menggunakan dataset sintetis untuk mendukung pengembangan dan pengujian sistem pengelolaan stok UMKM ROKKUS Mardani Raya.

Dataset yang digunakan mencakup:

- Dataset produk jadi yang disusun berdasarkan daftar menu untuk kebutuhan project.
- Dataset bahan baku yang berisi informasi persediaan bahan baku untuk simulasi pemantauan stok.
- Dataset transaksi produk yang digunakan untuk menggambarkan pergerakan stok produk jadi.

Data stok awal dan transaksi dibuat secara sintetis karena data operasional atau transaksi aktual tidak tersedia untuk pengolahan ini.

Dataset simulasi transaksi produk menggunakan periode 1–30 September 2026 dengan 300 transaksi buatan. Dataset produk jadi terdiri dari 29 produk, sedangkan dataset bahan baku terdiri dari 18 data bahan baku.

Perhitungan stok bahan baku menggunakan asumsi dan pemetaan kebutuhan bahan baku (BOM) sintetis. Oleh karena itu, hasilnya tidak dapat dianggap sebagai catatan penggunaan bahan baku aktual UMKM.

Seluruh angka stok, transaksi, ambang minimum, dan pemetaan BOM yang dibuat secara sintetis merupakan asumsi pengembangan. Data tersebut tidak merepresentasikan kondisi operasional atau penjualan aktual UMKM ROKKUS.

## 7. Tahapan Pengerjaan

1. Penyusunan master data produk.
2. Penyusunan dataset bahan baku.
3. Pembuatan dataset sintetis stok awal dan transaksi.
4. Data understanding dan pemeriksaan kualitas data.
5. Data preprocessing dan perhitungan stok.
6. Exploratory Data Analysis (EDA).
7. Klasifikasi status stok dengan pendekatan rule-based.
8. Evaluasi hasil klasifikasi.
9. Pembuatan visualisasi dan ringkasan dashboard.
10. Pengujian fungsional dataset.

## 8. Aturan Klasifikasi Simulasi

Klasifikasi status stok produk jadi menggunakan aturan berikut:

| Status | Aturan |
|---|---|
| Empty | Stok akhir sama dengan 0 |
| Low | Stok akhir 1 sampai 5 |
| Safe | Stok akhir lebih dari 5 |

Batas 5 unit merupakan asumsi untuk simulasi, bukan batas minimum resmi dari UMKM. Aturan perlu dikonfirmasi dengan pihak UMKM sebelum digunakan sebagai aturan operasional.

Klasifikasi saat ini berbasis aturan (rule-based), bukan model machine learning atau prediksi permintaan.

## 8A. Dua Skema Status Stok Produk Jadi

Project ini memakai dua skema status untuk produk jadi dengan tujuan berbeda. Keduanya dihitung dari stok akhir yang sama (total 332 unit).

| Skema | File | Aturan | Hasil |
|---|---|---|---|
| Batas tetap (utama, untuk integrasi aplikasi) | `dataset_stok_rokkus_final.csv`, `hasil_klasifikasi_stok_rokkus.csv`, `dashboard_summary_rokkus.csv` | Empty = 0, Low = 1-5, Safe > 5 | Safe 16, Low 8, Empty 5 |
| Batas per produk (`min_stock`) | `dataset_produk_jadi_final.csv`, notebook `ROKKUS_Data_Science.ipynb` | Habis = 0, Menipis <= min_stock, Aman > min_stock | Aman 20, Menipis 4, Habis 5 |

Pemetaan antar skema:

| Batas tetap | Batas per produk | Keterangan |
|---|---|---|
| Empty (5) | Habis (5) | Sama |
| Safe (16) | Aman (16) | Sama |
| Low (8) | Menipis (4) + Aman (4) | Selisih 4 produk (PR009, PR018, PR023, AD002) yang stok akhirnya 4-5 unit, di bawah batas tetap 5 tetapi masih di atas `min_stock` produknya |

Untuk integrasi dengan tim Full-stack dan Gen AI, gunakan skema batas tetap (Safe/Low/Empty). Skema `min_stock` dipakai untuk EDA dan simulasi batas minimum per produk. Kedua batas merupakan asumsi dan perlu dikonfirmasi dengan pihak UMKM.

## 9. Ringkasan Hasil Dataset Sintetis

Berdasarkan hasil pengolahan dan validasi dataset sintetis produk jadi:

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

Pengujian fungsional dilakukan untuk memastikan proses pengolahan dataset berjalan sesuai dengan aturan yang telah ditentukan.

Pengujian Data Preparation mencakup lima pemeriksaan:

1. Memastikan dataset tidak kosong.
2. Memastikan tidak terdapat stok akhir negatif.
3. Memastikan perhitungan stok akhir sesuai dengan rumus stok.
4. Memastikan seluruh produk memiliki klasifikasi status stok.
5. Memastikan hasil klasifikasi sesuai dengan aturan yang ditentukan.

Berdasarkan hasil pengujian terakhir pada Data Preparation, diperoleh:

- PASS: 5
- FAIL: 0

Pengujian Data Science dilakukan secara terpisah menggunakan pemeriksaan dataset dan hasil analisis. Berdasarkan hasil pengujian terakhir yang dijalankan:

- PASS: 12
- FAIL: 0

Pengujian perlu dijalankan kembali apabila dataset, proses preprocessing, atau aturan klasifikasi mengalami perubahan.

## 11. Output

Folder `outputs/` digunakan untuk menyimpan hasil pengolahan, visualisasi, dan pengujian, meliputi:

- `dashboard_summary_rokkus.csv`: ringkasan jumlah produk, stok akhir, stok masuk, stok keluar, dan distribusi status stok.
- `grafik_stok_per_kategori.png`: visualisasi total stok akhir berdasarkan kategori.
- `grafik_stok_masuk_keluar.png`: visualisasi perbandingan stok masuk dan stok keluar berdasarkan kategori.
- `grafik_distribusi_status.png`: visualisasi distribusi status stok produk.
- `eda_perbandingan_stok_produk.png`: visualisasi perbandingan stok produk.
- `eda_status_bahan_baku.png`: visualisasi status stok bahan baku.
- `eda_status_produk_jadi.png`: visualisasi status stok produk jadi.
- `eda_stok_akhir_bahan_baku.png`: visualisasi stok akhir bahan baku.
- `eda_stok_produk_per_kategori.png`: visualisasi stok produk berdasarkan kategori.
- `hasil_pengujian_fungsional.csv`: hasil pengujian fungsional Data Preparation.
- `hasil_pengujian_dataset_final.csv`: hasil pengujian dataset Data Science.

Seluruh output merupakan hasil pengolahan dataset sintetis dan disiapkan sebagai bahan pendukung pengembangan serta diskusi integrasi dengan tim Full-stack dan Gen AI.

---

**Project:** Pengembangan Aplikasi Pengelolaan dan Pemantauan Stok Harian Terintegrasi pada UMKM ROKKUS Mardani Raya

**Divisi:** Data Science