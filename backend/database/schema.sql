-- 1. Tabel Pengguna (Pengelola Stok & Pemilik)
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    nama VARCHAR(100) NOT NULL,
    username VARCHAR(50) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(20) NOT NULL CHECK (role IN ('pengelola_stok', 'pemilik')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2. Tabel Barang & Stok (tetap selaras dengan tabel items sebelumnya)
CREATE TABLE IF NOT EXISTS items (
    id SERIAL PRIMARY KEY,
    nama_barang VARCHAR(100) NOT NULL,
    kategori VARCHAR(50) NOT NULL,
    satuan VARCHAR(20) NOT NULL,
    stok_awal INTEGER NOT NULL DEFAULT 0 CHECK (stok_awal >= 0),
    stok_terkini INTEGER NOT NULL DEFAULT 0 CHECK (stok_terkini >= 0),
    batas_minimum INTEGER NOT NULL DEFAULT 10 CHECK (batas_minimum >= 0),
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 3. Tabel Riwayat Transaksi Stok Masuk & Keluar
CREATE TABLE IF NOT EXISTS stock_transactions (
    id SERIAL PRIMARY KEY,
    item_id INTEGER NOT NULL REFERENCES items(id) ON DELETE CASCADE,
    user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    tipe_transaksi VARCHAR(10) NOT NULL CHECK (tipe_transaksi IN ('masuk', 'keluar')),
    jumlah INTEGER NOT NULL CHECK (jumlah > 0),
    stok_sebelum INTEGER NOT NULL,
    stok_sesudah INTEGER NOT NULL,
    catatan TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 4. Tabel Riwayat Ringkasan Harian dari Generative AI
CREATE TABLE IF NOT EXISTS ai_summaries (
    id SERIAL PRIMARY KEY,
    ringkasan TEXT NOT NULL,
    sumber VARCHAR(50) DEFAULT 'generative_ai',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);