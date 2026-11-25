# ROKKUS Backend – REST API Pengelolaan Stok Harian

**Capstone Asah 2026 | Tim A26-CS159**  
Use Case: Aplikasi pengelolaan dan pemantauan stok harian UMKM ROKKUS Mardani Raya

---

## Deskripsi

Layanan backend berbasis **Express.js** dan **PostgreSQL** yang mengelola autentikasi pengguna, data stok barang, pencatatan transaksi masuk/keluar otomatis.

### Fitur Utama
- **Autentikasi & RBAC (JWT):** Membedakan hak akses antara `pengelola_stok` (CRUD & transaksi) dan `pemilik` (*read-only* dashboard & riwayat).
- **CRUD Stok Barang:** Pengelolaan barang beserta penanda status dasar (`habis`: stok = 0, `menipis`: stok ≤ batas minimum, `aman`: stok > batas minimum).
- **Transaksi Stok Otomatis:** Menggunakan PostgreSQL transaction (`BEGIN`/`COMMIT`/`ROLLBACK`) untuk memperbarui stok secara atomik dan menolak transaksi keluar jika stok tidak mencukupi.

---

## Struktur Direktori

```text
backend/
├── README.md
├── .env.example
├── .gitignore
├── package.json
├── database/
│   ├── schema.sql               ← Skema tabel PostgreSQL 
│   └── seedUsers.js             ← Seeder akun demo (pengelola & pemilik)
└── src/
    ├── index.js                 ← Entry point Express & registrasi routes
    ├── config/
    │   └── db.js                ← Konfigurasi pool PostgreSQL (lokal & DATABASE_URL)
    ├── controllers/
    │   ├── authController.js
    │   ├── stockController.js
    │   ├── transactionController.js
    │   └── dashboardController.js
    ├── middlewares/
    │   ├── authMiddleware.js    ← Verifikasi JWT & cek role
    │   └── validateMiddleware.js
    ├── routes/
    │   ├── authRoutes.js
    │   ├── stockRoutes.js
    │   ├── transactionRoutes.js
    │   └── dashboardRoutes.js
    └── validations/
        └── schemas.js           ← Skema validasi input Joi
```

---

## Setup & Instalasi

### Prasyarat
- Node.js ≥ 18
- PostgreSQL ≥ 15 (lokal atau cloud seperti Neon)

### 1. Instal Dependencies

```powershell
cd backend
npm install
```

### 2. Konfigurasi Environment

Salin `.env.example` menjadi `.env`, lalu sesuaikan nilainya:

```env
PORT=5000
DB_HOST=localhost
DB_PORT=5432
DB_USER=postgres
DB_PASSWORD=isi_password_postgres_anda
DB_NAME=rokkus_db
JWT_SECRET=isi_secret_key_anda
```

> Untuk deployment cloud (Neon/Render), cukup set `DATABASE_URL` menggantikan variabel `DB_*`.

### 3. Setup Database & Akun Demo

1. Buat database `rokkus_db` di PostgreSQL.
2. Jalankan query di `database/schema.sql` melalui pgAdmin / `psql` / SQL Editor.
3. Buat akun demo:

```powershell
npm run seed
```

**Akun Demo:**
| Peran | Username | Password | Hak Akses |
|---|---|---|---|
| Pengelola Stok | `pengelola` | `pengelola123` | CRUD barang, transaksi, dashboard |
| Pemilik | `pemilik` | `pemilik123` | Read-only stok, riwayat, dashboard |

---

## Cara Menjalankan

```powershell
# Mode development (auto-reload dengan nodemon)
npm run dev

# Mode production
npm start
```

Server berjalan di `http://localhost:5000`. Cek kesehatan server di `GET http://localhost:5000/api/v1/health`.

---

## Endpoint API

Semua endpoint (kecuali `/health` dan `/auth/login`) memerlukan header:
```http
Authorization: Bearer <jwt_token>
```

| Method | Path | Hak Akses | Deskripsi |
|---|---|---|---|
| `GET` | `/api/v1/health` | Publik | Cek status server |
| `POST` | `/api/v1/auth/login` | Publik | Login dan dapatkan token JWT |
| `GET` | `/api/v1/auth/me` | Semua peran | Detail pengguna yang sedang login |
| `GET` | `/api/v1/stocks` | Pengelola & Pemilik | Daftar stok barang + status dasar (dukung `?kategori=`) |
| `GET` | `/api/v1/stocks/:id` | Pengelola & Pemilik | Detail satu barang |
| `POST` | `/api/v1/stocks` | Pengelola Stok | Tambah barang baru beserta stok awal |
| `PUT` | `/api/v1/stocks/:id` | Pengelola Stok | Perbarui informasi barang |
| `DELETE` | `/api/v1/stocks/:id` | Pengelola Stok | Hapus barang |
| `GET` | `/api/v1/transactions` | Pengelola & Pemilik | Riwayat transaksi (dukung `?item_id=&tipe_transaksi=`) |
| `POST` | `/api/v1/transactions` | Pengelola Stok | Catat barang masuk/keluar & update stok otomatis |
| `GET` | `/api/v1/dashboard` | Pengelola & Pemilik | Ringkasan stok, 10 transaksi terakhir |

### Contoh Request Singkat

**Login (`POST /api/v1/auth/login`):**
```json
{
  "username": "pengelola",
  "password": "pengelola123"
}
```

**Catat Transaksi (`POST /api/v1/transactions`):**
```json
{
  "item_id": 1,
  "tipe_transaksi": "keluar",
  "jumlah": 10,
  "catatan": "Penjualan pagi"
}
```

### Status Code

| Code | Kondisi |
|---|---|
| `200` / `201` | Permintaan berhasil |
| `400` | Validasi Joi gagal atau stok tidak mencukupi |
| `401` | Token tidak ada, tidak valid, atau kedaluwarsa |
| `403` | Peran pengguna tidak memiliki izin akses |
| `404` | Data barang atau endpoint tidak ditemukan |
| `500` | Kesalahan internal server |


## Catatan Penting

1. **Data Sintetis:** Data barang dan transaksi menggunakan data *dummy* untuk keperluan prototipe dan demonstrasi (bukan data asli ROKKUS).
2. **Keamanan:** File `.env` dan folder `node_modules/` diabaikan oleh `.gitignore` dan tidak diunggah ke repositori.