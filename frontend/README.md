# ROKKUS Stok - Sistem Monitoring & Pencatatan Stok Roti Harian

> **Proyek Capstone Asah 2026**  
> **Tim:** A26-CS159  
> **Mitra UMKM:** ROKKUS Mardani Raya (Usaha kuliner roti kukus & bakar hijau pandan)  
> **Tipe Aplikasi:** Web Prototype Frontend (React + Vite + Tailwind CSS)

---

## 1. Deskripsi Proyek

**ROKKUS Stok** adalah aplikasi web prototipe operasional yang dirancang untuk mempermudah pencatatan dan monitoring stok roti pandan harian pada gerai ROKKUS Mardani Raya. 

Aplikasi ini berfokus pada efisiensi back-of-house gerai:
1. Memastikan pencatatan pasokan roti masuk dan roti keluar (penjualan) dilakukan secara cepat dan akurat.
2. Memberikan peringatan dini ketika stok roti berada pada level menipis atau habis.
3. Membantu pemilik usaha memantau kinerja operasional gerai dari jarak jauh tanpa risiko salah ubah data (akses *view-only*).

---

## 2. Akun Demo & Akses Peran (Roles)

Aplikasi memiliki 2 (dua) jenis peran pengguna dengan hak akses yang terpisah:

| Username | Nama Lengkap | Jabatan / Role | Hak Akses Utama |
| :--- | :--- | :--- | :--- |
| `pengelola` | **Budi Santoso** | Manajer Stok (`pengelola`) | Mengelola stok roti awal, mencatat pasokan masuk/keluar, mengelola daftar menu, mencatat belanja topping, mengubah status topping. |
| `pemilik` | **Arif** | Pemilik Usaha (`pemilik`) | **Strictly View-Only**. Melihat analitik visual dashboard, grafik tren menu terlaris, ringkasan AI harian, riwayat transaksi, dan status topping. Tidak ada tombol aksi tambah/ubah/hapus. |

> *Catatan Autentikasi Mock:* Pada mode mock, password dapat diisi dengan karakter apa saja minimal 4 karakter (misal: `demo123`). Sesi tersimpan di `localStorage` dan dilengkapi dialog konfirmasi saat *Keluar*.

---

## 3. Aturan Bisnis Utama (*Business Rules*)

Semua logika bisnis diletakkan pada layer layanan (`src/services/`) dan utilitas (`src/utils/`):

1. **Stok Roti Bersifat Tunggal (*One Single Stock*):**
   - Roti dihitung sebagai satu entitas tunggal: `"Roti Hijau Pandan"` dalam satuan **pcs**.
   - **Status Ketersediaan:**
     - **Habis:** Stok = 0 pcs.
     - **Menipis:** Stok < `LOW_STOCK_THRESHOLD` (default: 50 pcs).
     - **Aman:** Stok â‰¥ `LOW_STOCK_THRESHOLD`.
     - Ambang batas dapat disesuaikan di `src/config/constants.js`.
2. **Barang Masuk (Pasokan Roti):**
   - Menambah stok roti siap saji.
   - Kolom: Jumlah (> 0), Sesi (`Sesi 1` / `Sesi 2` / `Lainnya`), Tanggal (maksimal hari ini), Catatan opsional.
3. **Barang Keluar (Penjualan Menu):**
   - Mengurangi stok roti berdasarkan jumlah menu yang terjual.
   - **Aturan Pengurangan:** Total porsi dari menu **Roti Manis** dan **Roti Asin** langsung memotong stok roti.
   - **Pengecualian Tambahan:** Item kategori **Tambahan** (Keju Slice, Keju Parut, Telur, dll.) dicatat dalam rincian transaksi namun **TIDAK MENGURANGI** stok roti.
   - **Validasi Ketat:**
     - Minimal 1 menu dengan kuantitas > 0 dipilih (*"Pilih minimal satu menu"*).
     - Total roti keluar tidak boleh melebihi stok yang tersedia (*"Stok roti tidak mencukupi. Stok tersedia: X, jumlah diminta: Y"* dengan mempertahankan nilai input form).
4. **Stok Topping (Bahan Pelengkap):**
   - **Tidak memiliki angka sisa kuantitas** (bukan dihitung otomatis per gram/sendok).
   - Status diatur secara **manual** oleh Pengelola (`Aman`, `Hampir Habis`, `Habis`).
   - Dilengkapi riwayat pembelian belanja bahan (`tanggal beli`, `jumlah`, `satuan: pcs/toples/pack/kg`).
   - Menghitung **Rata-rata Beli Ulang** (*average repurchase interval*) otomatis di frontend berdasarkan selisih hari antar pembelian berturut-turut.
5. **Batasan Desain:**
   - Fokus operasional: Aplikasi khusus pencatatan kuantitas stok bahan dan porsi roti harian tanpa transaksi finansial.

---

## 4. Panduan Menjalankan Aplikasi

### Kebutuhan Sistem
- **Node.js** v18+ (disarankan v20+)
- **npm** v9+

### Langkah Instalasi
```bash
# 1. Masuk ke direktori proyek
cd rokkus-stok

# 2. Pasang dependensi
npm install

# 3. Jalankan server pengembang lokal
npm run dev
```

Aplikasi akan berjalan secara lokal di alamat: `http://localhost:5173`

### Membangun Versi Produksi (*Build*)
```bash
npm run build
npm run preview
```

---

## 5. Konfigurasi Lingkungan (`.env`) & Transisi ke Real API

Prototipe ini dirancang dengan pola *Adapter Service* sehingga sangat mudah dihubungkan dengan backend sesungguhnya (Node.js + Express + PostgreSQL).

### Konfigurasi `.env`
Salin template konfigurasi:
```bash
cp .env.example .env
```

Isi variabel:
```env
# Atur true untuk menggunakan In-Memory Mock Store (Default untuk demo)
# Atur false untuk menghubungkan ke REST API Backend sesungguhnya
VITE_USE_MOCK=true

# Alamat Base URL Server API Backend
VITE_API_BASE_URL=http://localhost:5000/api
```

### Cara Beralih dari Mock ke REST API Backend:
1. Rekan tim backend menyiapkan server REST API sesuai spesifikasi di dokumen [`docs/API_CONTRACT.md`](./docs/API_CONTRACT.md).
2. Ubah baris konfigurasi di file `.env`:
   ```env
   VITE_USE_MOCK=false
   VITE_API_BASE_URL=http://localhost:5000/api
   ```
3. Restart server Vite (`npm run dev`). Seluruh fungsi di `src/services/*.js` secara otomatis memanggil endpoint REST API via `fetch` lengkap dengan token otorisasi header `Authorization: Bearer <token>`.

### Parameter Pengujian / Dev Switches (URL Parameters)
Untuk keperluan pengujian demo dan evaluasi *edge cases*, aplikasi menyediakan 3 (tiga) switch simulasi via query parameter URL:
1. `?simulateAiFail=1`: Mensimulasikan kegagalan layanan AI pada Dashboard Pemilik. Kartu AI menampilkan status *fallback* *"Layanan AI tidak tersedia. Stok dan riwayat transaksi tetap dapat dilihat."* sementara modul lainnya di dashboard tetap berfungsi normal.
2. `?simulateSaveFail=1`: Mensimulasikan kegagalan penyimpanan saat menyimpan transaksi (Barang Keluar / Barang Masuk) maupun belanja topping. Sistem memunculkan alert *"Transaksi gagal disimpan. Silakan coba lagi."* yang memiliki visual kontras dari validasi stok dan tetap mempertahankan seluruh nilai input formulir yang telah diisi.
3. `?simulateLoadFail=1`: Mensimulasikan kegagalan jaringan saat memuat data di seluruh layar data. Menampilkan kartu state error *"Gagal memuat data. Periksa koneksi lalu coba lagi."* dengan tombol interaktif *"Coba Lagi"*.

---

## 6. Struktur Direktori Proyek

```
rokkus-stok/
â”œâ”€â”€ docs/
â”‚   â””â”€â”€ API_CONTRACT.md       # Dokumentasi spesifikasi JSON request/response API
â”œâ”€â”€ src/
â”‚   â”œâ”€â”€ assets/               # Aset gambar & logo resmi ROKKUS (logo.png)
â”‚   â”œâ”€â”€ components/           # Komponen UI modular (StatusBadge, StockCard, Modal, MenuCard, dll.)
â”‚   â”œâ”€â”€ config/               # Konstanta sistem (LOW_STOCK_THRESHOLD, roles, kategori)
â”‚   â”œâ”€â”€ context/              # State autentikasi (AuthContext) & ToastContext
â”‚   â”œâ”€â”€ layouts/              # Layout shell dengan sidebar hijau brand responsif
â”‚   â”œâ”€â”€ mocks/                # Data seed prototipe (roti, menu, topping, transaksi)
â”‚   â”œâ”€â”€ pages/                # Halaman aplikasi (Login, DaftarStok, CatatTransaksi, Riwayat, Topping, Dashboard)
â”‚   â”œâ”€â”€ routes/               # Routing & Role-Based Protected Route Guard
â”‚   â”œâ”€â”€ services/             # Layer data (mock store & apiClient REST handoff)
â”‚   â””â”€â”€ utils/                # Fungsi kalkulasi stok & formatting tanggal Indonesia
â”œâ”€â”€ .env.example              # Contoh variabel environment
â”œâ”€â”€ tailwind.config.js       # Token warna brand (Dark Green, Light Green, Mustard, Cream)
â””â”€â”€ package.json
```

---

## 7. Checklist Fitur Prototipe

- [x] **Autentikasi & Otorisasi:**
  - Login split panel dengan panel brand hijau & demo account quick filler.
  - Route Guard berbasis role (`pengelola` vs `pemilik`).
  - Halaman khusus `Akses Ditolak` jika mencoba membuka rute terlarang.
  - Dialog konfirmasi logout.
- [x] **Daftar Stok (Pengelola):**
  - Kartu indikator besar stok roti pandan (sisa stok, status Aman/Menipis/Habis, masuk/keluar hari ini).
  - Modal "Ubah Stok Awal" untuk sinkronisasi fisik gerai.
  - Tabel Daftar Menu dengan tab kategori, pencarian, badge Best Seller / Baru.
  - Tambah, Ubah, dan Hapus menu dengan konfirmasi aman.
- [x] **Catat Transaksi (Pengelola):**
  - Tab Barang Keluar & Barang Masuk.
  - Stepper `- / +` dan input langsung pada setiap kartu menu.
  - Best Seller ditampilkan pertama di setiap kelompok.
  - Validasi stok tidak mencukupi & minimal 1 menu dengan form value retention.
  - Sticky bottom summary bar dengan live calculation dan ringkasan menu terpilih.
  - Logika khusus: Kategori Tambahan tidak memotong stok roti.
- [x] **Riwayat Transaksi (Pengelola & Pemilik):**
  - Tab Riwayat Transaksi Roti dan Riwayat Pembelian Topping.
  - Filter jenis transaksi, rentang tanggal, dan pencarian teks.
  - Paginasi data dan skeleton loaders.
- [x] **Stok Topping:**
  - Status manual Aman / Hampir Habis / Habis.
  - Pengelola dapat mencatat pembelian baru dan mengubah status.
  - Pemilik murni *view-only* tanpa tombol manipulasi data.
  - Perhitungan otomatis rata-rata hari pembelian ulang.
- [x] **Dashboard Pemilik:**
  - Kartu metrik KPI harian.
  - Horizontal Bar Chart penjualan per menu hari ini.
  - Tabel 5 transaksi terbaru dengan shortcut ke halaman riwayat.
  - Kartu Ringkasan Harian AI dengan *error boundary* independen & dev simulator `?simulateAiFail=1`.
- [x] **Kesiapan Handoff Backend:**
  - Seluruh akses data melalui layer `src/services/*.js`.
  - Kontrak API terdokumentasi lengkap di `docs/API_CONTRACT.md`.

---

## 8. Batasan Luar Ruang Lingkup (*Out of Scope*)
- Implementasi backend server nyata & database PostgreSQL (dikerjakan terpisah oleh anggota tim backend).
- Transaksi finansial, sistem pembayaran, dan layanan pesan-antar pihak ketiga.
- Model AI/ML real-time (menggunakan data ringkasan analitik simulasi terstruktur).
