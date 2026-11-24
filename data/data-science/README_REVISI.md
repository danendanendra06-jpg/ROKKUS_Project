# Revisi Lanjutan Dataset Data Science ROKKUS

## Dataset bahan baku
`dataset_bahan_baku_final.csv` sekarang memuat `category` agar EDA kategori tidak memerlukan merge dengan master.
Ambang `min_stock` disesuaikan untuk simulasi monitoring: BB002, BB013, BB014, dan BB018 ditetapkan Menipis; bahan lain menggunakan ambang 50% stok akhir. Ini adalah skenario ambang simulasi, bukan aturan resmi UMKM. Tidak ada stok yang dibuat nol, sehingga tidak ada status Habis.

## Dataset produk jadi
`dataset_produk_jadi_final.csv` dibuat dari `dataset_stok_rokkus_final.csv` yang diberikan. `min_stock` dihitung sebagai tiga hari rata-rata pengeluaran produk (total_keluar/30 x 3), dibulatkan ke atas. `stock_status` distandardisasi menjadi Aman/Menipis/Habis. Ini merupakan aturan simulasi dan perlu disepakati tim.

## Data Dictionary
Semua Data Dictionary menggunakan header persis: `Nama Kolom`, `Tipe Data`, `Keterangan`, `Contoh`.
File yang disediakan:
- `data_dictionary_transaksi_bahan_baku.csv`
- `data_dictionary_dataset_bahan_baku_final.csv`
- `data_dictionary_produk_jadi.csv`
- `data_dictionary_transaksi_produk.csv`

## Sinkronisasi bahan baku
Transaksi bahan baku sebelumnya dihitung dari transaksi produk jadi `KELUAR` dikalikan takaran BOM sintetis. AD004 masih belum memiliki pemetaan bahan baku dan perlu keputusan tim.
