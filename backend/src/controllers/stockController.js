const pool = require('../config/db');

const STATUS_SQL = `
  CASE 
    WHEN stok_terkini = 0 THEN 'habis'
    WHEN stok_terkini <= batas_minimum THEN 'menipis'
    ELSE 'aman'
  END AS status_dasar
`;

// GET /api/v1/stocks
const getAllStocks = async (req, res) => {
  try {
    const { kategori } = req.query;
    const values = [];
    let whereClause = '';

    if (kategori) {
      values.push(kategori);
      whereClause = `WHERE LOWER(kategori) = LOWER($1)`;
    }

    const query = `
      SELECT 
        id, nama_barang, kategori, satuan,
        stok_awal, stok_terkini, batas_minimum,
        ${STATUS_SQL},
        updated_at
      FROM items
      ${whereClause}
      ORDER BY id ASC
    `;

    const result = await pool.query(query, values);

    return res.status(200).json({
      status: 'success',
      message: 'Data stok barang berhasil diambil',
      total: result.rowCount,
      data: result.rows,
    });
  } catch (error) {
    console.error('Error getAllStocks:', error);
    return res.status(500).json({
      status: 'error',
      message: 'Gagal mengambil data stok barang dari server',
    });
  }
};

// GET /api/v1/stocks/:id
const getStockById = async (req, res) => {
  const { id } = req.params;
  try {
    const result = await pool.query(
      `SELECT id, nama_barang, kategori, satuan, stok_awal, stok_terkini, batas_minimum, ${STATUS_SQL}, updated_at
       FROM items WHERE id = $1`,
      [id]
    );

    if (result.rowCount === 0) {
      return res.status(404).json({
        status: 'fail',
        message: 'Barang tidak ditemukan',
      });
    }

    return res.status(200).json({
      status: 'success',
      data: result.rows[0],
    });
  } catch (error) {
    console.error('Error getStockById:', error);
    return res.status(500).json({
      status: 'error',
      message: 'Gagal mengambil detail barang',
    });
  }
};

// POST /api/v1/stocks
const createStock = async (req, res) => {
  const { nama_barang, kategori, satuan, stok_awal, batas_minimum } = req.body;

  try {
    const query = `
      INSERT INTO items (nama_barang, kategori, satuan, stok_awal, stok_terkini, batas_minimum)
      VALUES ($1, $2, $3, $4, $4, $5)
      RETURNING id, nama_barang, kategori, satuan, stok_awal, stok_terkini, batas_minimum, ${STATUS_SQL}, updated_at
    `;

    const result = await pool.query(query, [
      nama_barang,
      kategori,
      satuan,
      stok_awal,
      batas_minimum,
    ]);

    return res.status(201).json({
      status: 'success',
      message: 'Barang baru berhasil ditambahkan',
      data: result.rows[0],
    });
  } catch (error) {
    console.error('Error createStock:', error);
    return res.status(500).json({
      status: 'error',
      message: 'Gagal menambahkan barang baru',
    });
  }
};

// PUT /api/v1/stocks/:id
const updateStock = async (req, res) => {
  const { id } = req.params;
  const { nama_barang, kategori, satuan, stok_awal, stok_terkini, batas_minimum } = req.body;

  try {
    const query = `
      UPDATE items
      SET
        nama_barang = COALESCE($1, nama_barang),
        kategori = COALESCE($2, kategori),
        satuan = COALESCE($3, satuan),
        stok_awal = COALESCE($4, stok_awal),
        stok_terkini = COALESCE($5, stok_terkini),
        batas_minimum = COALESCE($6, batas_minimum),
        updated_at = CURRENT_TIMESTAMP
      WHERE id = $7
      RETURNING id, nama_barang, kategori, satuan, stok_awal, stok_terkini, batas_minimum, ${STATUS_SQL}, updated_at
    `;

    const result = await pool.query(query, [
      nama_barang ?? null,
      kategori ?? null,
      satuan ?? null,
      stok_awal ?? null,
      stok_terkini ?? null,
      batas_minimum ?? null,
      id,
    ]);

    if (result.rowCount === 0) {
      return res.status(404).json({
        status: 'fail',
        message: 'Barang tidak ditemukan',
      });
    }

    return res.status(200).json({
      status: 'success',
      message: 'Data barang berhasil diperbarui',
      data: result.rows[0],
    });
  } catch (error) {
    console.error('Error updateStock:', error);
    return res.status(500).json({
      status: 'error',
      message: 'Gagal memperbarui data barang',
    });
  }
};

// DELETE /api/v1/stocks/:id
const deleteStock = async (req, res) => {
  const { id } = req.params;

  try {
    const result = await pool.query(
      'DELETE FROM items WHERE id = $1 RETURNING id, nama_barang',
      [id]
    );

    if (result.rowCount === 0) {
      return res.status(404).json({
        status: 'fail',
        message: 'Barang tidak ditemukan',
      });
    }

    return res.status(200).json({
      status: 'success',
      message: `Barang "${result.rows[0].nama_barang}" berhasil dihapus`,
    });
  } catch (error) {
    console.error('Error deleteStock:', error);
    return res.status(500).json({
      status: 'error',
      message: 'Gagal menghapus data barang',
    });
  }
};

module.exports = {
  getAllStocks,
  getStockById,
  createStock,
  updateStock,
  deleteStock,
};