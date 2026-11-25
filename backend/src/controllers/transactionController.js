const pool = require('../config/db');

// GET /api/v1/transactions
const getAllTransactions = async (req, res) => {
  try {
    const { item_id, tipe_transaksi } = req.query;
    const conditions = [];
    const values = [];

    if (item_id) {
      values.push(item_id);
      conditions.push(`t.item_id = $${values.length}`);
    }

    if (tipe_transaksi && ['masuk', 'keluar'].includes(tipe_transaksi)) {
      values.push(tipe_transaksi);
      conditions.push(`t.tipe_transaksi = $${values.length}`);
    }

    const whereClause = conditions.length > 0 ? `WHERE ${conditions.join(' AND ')}` : '';

    const query = `
      SELECT 
        t.id,
        t.item_id,
        i.nama_barang,
        i.satuan,
        t.tipe_transaksi,
        t.jumlah,
        t.stok_sebelum,
        t.stok_sesudah,
        t.catatan,
        u.nama AS dicatat_oleh,
        t.created_at
      FROM stock_transactions t
      JOIN items i ON t.item_id = i.id
      LEFT JOIN users u ON t.user_id = u.id
      ${whereClause}
      ORDER BY t.created_at DESC, t.id DESC
    `;

    const result = await pool.query(query, values);

    return res.status(200).json({
      status: 'success',
      message: 'Riwayat transaksi stok berhasil diambil',
      total: result.rowCount,
      data: result.rows,
    });
  } catch (error) {
    console.error('Error getAllTransactions:', error);
    return res.status(500).json({
      status: 'error',
      message: 'Gagal mengambil riwayat transaksi stok',
    });
  }
};

// POST /api/v1/transactions
const createTransaction = async (req, res) => {
  const { item_id, tipe_transaksi, jumlah, catatan } = req.body;
  const userId = req.user.id;

  const client = await pool.connect();

  try {
    await client.query('BEGIN');

    const itemResult = await client.query(
      'SELECT id, nama_barang, satuan, stok_terkini, batas_minimum FROM items WHERE id = $1 FOR UPDATE',
      [item_id]
    );

    if (itemResult.rowCount === 0) {
      await client.query('ROLLBACK');
      return res.status(404).json({
        status: 'fail',
        message: 'Barang tidak ditemukan',
      });
    }

    const item = itemResult.rows[0];
    const stokSebelum = item.stok_terkini;

    if (tipe_transaksi === 'keluar' && jumlah > stokSebelum) {
      await client.query('ROLLBACK');
      return res.status(400).json({
        status: 'fail',
        message: `Stok "${item.nama_barang}" tidak mencukupi. Stok tersedia: ${stokSebelum} ${item.satuan}, diminta keluar: ${jumlah} ${item.satuan}.`,
      });
    }

    const stokSesudah =
      tipe_transaksi === 'masuk' ? stokSebelum + jumlah : stokSebelum - jumlah;

    await client.query(
      'UPDATE items SET stok_terkini = $1, updated_at = CURRENT_TIMESTAMP WHERE id = $2',
      [stokSesudah, item_id]
    );

    const trxResult = await client.query(
      `INSERT INTO stock_transactions 
        (item_id, user_id, tipe_transaksi, jumlah, stok_sebelum, stok_sesudah, catatan)
       VALUES ($1, $2, $3, $4, $5, $6, $7)
       RETURNING *`,
      [item_id, userId, tipe_transaksi, jumlah, stokSebelum, stokSesudah, catatan]
    );

    await client.query('COMMIT');

    return res.status(201).json({
      status: 'success',
      message: `Transaksi barang ${tipe_transaksi} berhasil dicatat dan stok diperbarui otomatis`,
      data: {
        transaksi: trxResult.rows[0],
        barang: {
          id: item.id,
          nama_barang: item.nama_barang,
          satuan: item.satuan,
          stok_terkini: stokSesudah,
        },
      },
    });
  } catch (error) {
    await client.query('ROLLBACK');
    console.error('Error createTransaction:', error);
    return res.status(500).json({
      status: 'error',
      message: 'Gagal memproses transaksi stok',
    });
  } finally {
    client.release();
  }
};

module.exports = { getAllTransactions, createTransaction };