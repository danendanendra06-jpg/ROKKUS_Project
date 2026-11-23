# API Contract - ROKKUS Stok

Dokumen ini mendefinisikan spesifikasi kontrak REST API untuk menghubungkan Frontend **ROKKUS Stok** dengan Backend (Node.js + Express + PostgreSQL).

Base URL default: `http://localhost:5000/api`  
Format data: `application/json`  
Autentikasi: Header `Authorization: Bearer <token>` (didapat setelah login).

---

## 1. Autentikasi (`/auth`)

### `POST /auth/login`
Autentikasi pengguna gerai.

- **Request Body**:
```json
{
  "username": "pengelola",
  "password": "password123"
}
```

- **Response `200 OK`**:
```json
{
  "token": "jwt-token-string",
  "user": {
    "username": "pengelola",
    "name": "Budi Santoso",
    "role": "pengelola",
    "title": "Manajer Stok"
  }
}
```

- **Response `400 Bad Request`**:
```json
{
  "message": "Username atau password salah. Silakan coba lagi."
}
```

---

### `POST /auth/logout`
Mengakhiri sesi pengguna.

- **Request Headers**: `Authorization: Bearer <token>`
- **Response `200 OK`**:
```json
{
  "success": true,
  "message": "Berhasil keluar"
}
```

---

## 2. Stok Roti (`/stock`)

### `GET /stock/bread`
Mengambil status dan kuantitas sisa stok roti hijau pandan.

- **Response `200 OK`**:
```json
{
  "name": "Roti Hijau Pandan",
  "unit": "pcs",
  "stock": 45,
  "initialStock": 0,
  "masukHariIni": 100,
  "keluarHariIni": 55,
  "updatedAt": "2026-11-21 16:45"
}
```

---

### `PATCH /stock/bread/initial`
Memperbarui stok awal roti untuk rekalkulasi sisa stok.

- **Request Body**:
```json
{
  "initialStock": 50
}
```

- **Response `200 OK`**:
```json
{
  "name": "Roti Hijau Pandan",
  "unit": "pcs",
  "stock": 95,
  "initialStock": 50,
  "masukHariIni": 100,
  "keluarHariIni": 55
}
```

---

## 3. Manajemen Menu (`/menu-items`)

### `GET /menu-items`
Mengambil daftar menu. Opsional query parameter: `?category=Roti%20Manis`.

- **Response `200 OK`**:
```json
[
  {
    "id": "m-1",
    "name": "Lotus Biscoff",
    "category": "Roti Manis",
    "tag": "Baru",
    "todaySales": 2
  },
  {
    "id": "m-2",
    "name": "Coklat Keju",
    "category": "Roti Manis",
    "tag": "Best Seller",
    "todaySales": 10
  }
]
```

---

### `POST /menu-items`
Menambahkan menu baru.

- **Request Body**:
```json
{
  "name": "Greentea Keju",
  "category": "Roti Manis",
  "tag": "Baru"
}
```

- **Response `201 Created`**:
```json
{
  "id": "m-12345",
  "name": "Greentea Keju",
  "category": "Roti Manis",
  "tag": "Baru",
  "todaySales": 0
}
```

---

### `PUT /menu-items/:id`
Mengubah data menu yang sudah ada.

- **Request Body**:
```json
{
  "name": "Greentea Keju Spesial",
  "category": "Roti Manis",
  "tag": "Best Seller"
}
```

- **Response `200 OK`**:
```json
{
  "id": "m-12345",
  "name": "Greentea Keju Spesial",
  "category": "Roti Manis",
  "tag": "Best Seller"
}
```

---

### `DELETE /menu-items/:id`
Menghapus menu dari daftar.

- **Response `200 OK`**:
```json
{
  "success": true,
  "message": "Menu berhasil dihapus"
}
```

---

## 4. Transaksi Stok (`/transactions`)

### `POST /transactions`
Mencatat transaksi barang keluar (penjualan) atau barang masuk (pasokan).

#### A. Transaksi Barang Keluar
*Aturan Bisnis:* Kategori `Roti Manis` dan `Roti Asin` memotong stok roti. Kategori `Tambahan` dicatat namun **tidak** mengurangi stok roti.

- **Request Body**:
```json
{
  "type": "keluar",
  "date": "2026-11-21",
  "cookingMethod": "Kukus",
  "note": "Pesanan pelanggan hangat",
  "items": [
    { "menuItemId": "m-8", "qty": 4 },
    { "menuItemId": "m-18", "qty": 2 },
    { "menuItemId": "m-26", "qty": 1 }
  ]
}
```

- **Response `201 Created`**:
```json
{
  "success": true,
  "currentStock": 39,
  "transaction": {
    "id": "trx-9999",
    "datetime": "2026-11-21 16:50",
    "date": "2026-11-21",
    "type": "keluar",
    "totalQty": 6,
    "details": "Coklat Crunchy 4, Telur Mayo 2, Keju Slice 1 (Tambahan)",
    "cookingMethod": "Kukus",
    "stockAfter": 39,
    "recordedBy": "Budi Santoso",
    "note": "Pesanan pelanggan hangat"
  }
}
```

- **Response `400 Bad Request` (Stok Tidak Mencukupi)**:
```json
{
  "code": "INSUFFICIENT_STOCK",
  "message": "Stok roti tidak mencukupi. Stok tersedia: 12, jumlah diminta: 20.",
  "available": 12,
  "requested": 20
}
```

#### B. Transaksi Barang Masuk
- **Request Body**:
```json
{
  "type": "masuk",
  "date": "2026-11-21",
  "session": "Sesi 1",
  "qty": 50,
  "note": "Pasokan batch pagi"
}
```

- **Response `201 Created`**:
```json
{
  "success": true,
  "currentStock": 95,
  "transaction": {
    "id": "trx-10000",
    "datetime": "2026-11-21 08:00",
    "date": "2026-11-21",
    "type": "masuk",
    "totalQty": 50,
    "details": "Sesi 1 - Pasokan Roti",
    "session": "Sesi 1",
    "cookingMethod": "-",
    "stockAfter": 95,
    "recordedBy": "Budi Santoso",
    "note": "Pasokan batch pagi"
  }
}
```

---

### `GET /transactions`
Mengambil riwayat transaksi dengan filter dan paginasi.
Query parameters:
- `type`: `masuk` | `keluar`
- `from`: YYYY-MM-DD
- `to`: YYYY-MM-DD
- `q`: string pencarian
- `page`: integer (default: 1)
- `limit`: integer (default: 10)

- **Response `200 OK`**:
```json
{
  "items": [
    {
      "id": "trx-12",
      "datetime": "2026-11-21 16:30",
      "date": "2026-11-21",
      "type": "keluar",
      "totalQty": 6,
      "details": "Coklat Crunchy 4, Telur Mayo 2",
      "cookingMethod": "Kukus",
      "stockAfter": 45,
      "recordedBy": "Budi Santoso",
      "note": "Pelanggan minta kukus hangat"
    }
  ],
  "total": 12,
  "page": 1,
  "limit": 10,
  "totalPages": 2
}
```

---

## 5. Stok & Pembelian Topping (`/toppings`)

### `GET /toppings`
Mengambil data topping beserta riwayat pembelian masing-masing.

- **Response `200 OK`**:
```json
[
  {
    "id": "top-1",
    "name": "Coklat",
    "status": "Aman",
    "purchases": [
      {
        "id": "tp-101",
        "date": "2026-11-14",
        "qty": 5,
        "unit": "kg",
        "recordedBy": "Budi Santoso"
      }
    ]
  }
]
```

---

### `PATCH /toppings/:id/status`
Memperbarui status manual topping (`Aman` | `Hampir Habis` | `Habis`).

- **Request Body**:
```json
{
  "status": "Hampir Habis"
}
```

- **Response `200 OK`**:
```json
{
  "id": "top-1",
  "name": "Coklat",
  "status": "Hampir Habis"
}
```

---

### `POST /topping-purchases`
Mencatat pembelian bahan pelengkap / topping baru.

- **Request Body**:
```json
{
  "toppingId": "top-1",
  "date": "2026-11-21",
  "qty": 5,
  "unit": "kg"
}
```

- **Response `201 Created`**:
```json
{
  "success": true,
  "purchase": {
    "id": "tp-200",
    "date": "2026-11-21",
    "qty": 5,
    "unit": "kg",
    "recordedBy": "Budi Santoso"
  }
}
```

---

### `GET /topping-purchases`
Mengambil seluruh riwayat pembelian topping secara kronologis menurun.

- **Response `200 OK`**:
```json
[
  {
    "id": "tp-200",
    "toppingId": "top-1",
    "toppingName": "Coklat",
    "date": "2026-11-21",
    "qty": 5,
    "unit": "kg",
    "recordedBy": "Budi Santoso"
  }
]
```

---

## 6. Dashboard Pemilik (`/dashboard`)

### `GET /dashboard/summary`
Mengambil data agregasi stok hari ini, top sales per menu, dan riwayat terbaru.

- **Response `200 OK`**:
```json
{
  "stock": 45,
  "masukHariIni": 100,
  "keluarHariIni": 55,
  "topSales": [
    { "name": "Coklat Crunchy", "category": "Roti Manis", "sales": 14 },
    { "name": "Coklat Keju", "category": "Roti Manis", "sales": 10 },
    { "name": "Nutella Keju", "category": "Roti Manis", "sales": 7 },
    { "name": "Telur Mayo", "category": "Roti Asin", "sales": 6 },
    { "name": "Beef Mayo", "category": "Roti Asin", "sales": 5 }
  ],
  "recentTransactions": [
    {
      "id": "trx-12",
      "datetime": "2026-11-21 16:30",
      "type": "keluar",
      "totalQty": 6,
      "details": "Coklat Crunchy 4, Telur Mayo 2",
      "recordedBy": "Budi Santoso"
    }
  ]
}
```

---

### `GET /dashboard/ai-summary`
Endpoint independen untuk ringkasan dan rekomendasi operasional dari analisis AI.
Query parameter pendukung dev: `?simulateAiFail=1`.

- **Response `200 OK`**:
```json
{
  "generatedAt": "2026-11-21T16:50:00Z",
  "summary": "Tren stok roti hijau pandan hari ini berjalan dinamis dengan serapan tertinggi pada varian Coklat Crunchy (14 pcs) dan Coklat Keju (10 pcs). Sisa stok berada di level 45 pcs (Status Menipis), disarankan melakukan persiapan pasokan roti sesi sore/malam untuk menjaga ketersediaan hingga jam operasional berakhir.",
  "recommendations": [
    "Persiapkan pasokan sesi sore minimal 40-50 pcs untuk mengantisipasi rush hour malam.",
    "Topping Nutella berstatus Habis dan Keju Parut Hampir Habis; jadwalkan pembelian ulang segera."
  ]
}
```

- **Response `503 Service Unavailable`** (jika layanan AI offline):
```json
{
  "message": "Layanan AI tidak tersedia. Stok dan riwayat transaksi tetap dapat dilihat."
}
```
*(Catatan: Kegagalan endpoint ini tidak boleh memblokir atau menggagalkan pemuatan data dashboard lainnya).*
