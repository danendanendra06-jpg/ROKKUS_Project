# Data Preprocessing -- UMKM ROKKUS Mardani Raya

Folder ini berisi notebook dan hasil pengolahan data persediaan untuk
proyek Capstone UMKM ROKKUS Mardani Raya.

## Tujuan

Melakukan pemeriksaan kualitas data, pembersihan, penggabungan,
klasifikasi status stok, dan analisis persediaan produk sebagai
persiapan untuk tahapan pengembangan AI berikutnya.

## Dataset

Dataset yang digunakan merupakan **dataset sintetis**, bukan catatan
transaksi operasional aktual UMKM ROKKUS. Periode data yang
disimulasikan adalah 1--30 September 2026.

Terdapat tiga dataset sumber: - Master produk: 29 baris, 4 kolom. - Stok
awal: 29 baris, 5 kolom. - Transaksi stok: 300 baris, 5 kolom.

Data sumber ditanam langsung di dalam notebook menggunakan representasi
Base64, sehingga notebook tidak memerlukan proses `files.upload()` atau
pembacaan CSV input dari folder lokal.

## Struktur Folder

``` text
data-preprocessing/
├── README.md
├── notebooks/
│   └── ROKKUS_Data_Wrangling_Preprocessing.ipynb
├── data/
│   └── processed/
│       └── dataset_stok_rokkus_clean.csv
└── outputs/
    ├── analisis_stok_per_kategori.csv
    ├── hasil_data_quality.csv
    ├── produk_low_empty.csv
    ├── ringkasan_preprocessing.csv
    └── ringkasan_status_stok.csv
```

## Tahapan Pengolahan

1.  Import library dan pemuatan dataset.
2.  Pemeriksaan kualitas data (Data Quality).
3.  Data cleaning.
4.  Data wrangling dan perhitungan stok akhir.
5.  Klasifikasi status stok.
6.  Analisis hasil dan temuan bisnis.
7.  Visualisasi hasil analisis.
8.  Penyimpanan dan validasi output.

## Definisi Status Stok

Klasifikasi yang digunakan dalam analisis ini merupakan asumsi untuk
dataset sintetis: - **Empty:** stok akhir = 0. - **Low:** stok akhir
1--5. - **Safe:** stok akhir \> 5.

Batas tersebut bukan kebijakan resmi UMKM ROKKUS dan perlu dikonfirmasi
apabila akan digunakan pada data operasional.

## Ringkasan Hasil

Berdasarkan hasil pengolahan dataset sintetis: - Total stok awal: 608
unit. - Total stok masuk: 620 unit. - Total stok keluar: 896 unit. -
Total stok akhir: 332 unit. - Status Safe: 16 produk. - Status Low: 8
produk. - Status Empty: 5 produk.

## Cara Menjalankan

1.  Buka file notebook pada folder `notebooks/` menggunakan Google Colab
    atau Jupyter Notebook.
2.  Jalankan sel dari awal secara berurutan.
3.  Notebook memuat dataset sumber yang telah ditanam di dalam kode,
    sehingga tidak perlu mengunggah file CSV input secara manual.
4.  File CSV hasil pengolahan disimpan ke folder `data/processed/` dan
    `outputs/` pada lingkungan kerja notebook.

## Catatan

Hasil analisis hanya menggambarkan dataset sintetis untuk kebutuhan
pengembangan dan pengujian proyek. Hasil ini tidak boleh dianggap
sebagai kondisi stok aktual UMKM ROKKUS Mardani Raya tanpa verifikasi
menggunakan data operasional.
