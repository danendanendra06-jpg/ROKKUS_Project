const axios = require('axios');
const pool = require('../config/db');

const getDashboardData = async (req, res) => {
  try {
    const stocksResult = await pool.query(`
      SELECT 
        id, nama_barang, kategori, satuan,
        stok_awal, stok_terkini, batas_minimum,
        CASE 
          WHEN stok_terkini = 0 THEN 'habis'
          WHEN stok_terkini <= batas_minimum THEN 'menipis'
          ELSE 'aman'
        END AS status_dasar,
        updated_at
      FROM items
      ORDER BY id ASC
    `);

    const recentTrxResult = await pool.query(`
      SELECT 
        t.id, t.item_id, i.nama_barang, i.satuan,
        t.tipe_transaksi, t.jumlah, t.stok_sebelum, t.stok_sesudah,
        t.catatan, u.nama AS dicatat_oleh, t.created_at
      FROM stock_transactions t
      JOIN items i ON t.item_id = i.id
      LEFT JOIN users u ON t.user_id = u.id
      ORDER BY t.created_at DESC, t.id DESC
      LIMIT 10
    `);

    const items = stocksResult.rows;
    const recentTransactions = recentTrxResult.rows;

    const ringkasanStok = {
      total_barang: items.length,
      stok_aman: items.filter((i) => i.status_dasar === 'aman').length,
      stok_menipis: items.filter((i) => i.status_dasar === 'menipis').length,
      stok_habis: items.filter((i) => i.status_dasar === 'habis').length,
    };

    let aiClassification = null;
    let aiSummary = null;
    let aiStatus = 'available';
    let aiMessage = 'Layanan AI aktif';

    const fastApiUrl = process.env.FASTAPI_URL;

    if (fastApiUrl) {
      try {
        // Sesuaikan path endpoint & payload ini dengan kontrak API tim AI (Danendra)
        const [mlResponse, genAiResponse] = await Promise.all([
          axios.post(`${fastApiUrl}/predict-status`, { items }, { timeout: 5000 }),
          axios.post(
            `${fastApiUrl}/generate-summary`,
            { items, recent_transactions: recentTransactions },
            { timeout: 8000 }
          ),
        ]);

        aiClassification = mlResponse.data;
        aiSummary = genAiResponse.data?.summary || genAiResponse.data?.ringkasan || null;

        if (aiSummary) {
          await pool.query(
            'INSERT INTO ai_summaries (ringkasan, sumber) VALUES ($1, $2)',
            [aiSummary, 'generative_ai']
          );
        }
      } catch (aiError) {
        console.warn('Layanan AI tidak dapat diakses:', aiError.message);
        aiStatus = 'unavailable';
        aiMessage = 'Layanan AI tidak tersedia';
      }
    } else {
      aiStatus = 'unavailable';
      aiMessage = 'Layanan AI tidak tersedia';
    }

    const savedSummaries = await pool.query(
      'SELECT id, ringkasan, created_at FROM ai_summaries ORDER BY created_at DESC LIMIT 5'
    );

    return res.status(200).json({
      status: 'success',
      message: 'Data dashboard berhasil diambil',
      data: {
        ringkasan_stok: ringkasanStok,
        daftar_stok: items,
        riwayat_transaksi_terbaru: recentTransactions,
        ai: {
          status: aiStatus,
          message: aiMessage,
          klasifikasi_status: aiClassification,
          ringkasan_harian: aiSummary,
          riwayat_ringkasan: savedSummaries.rows,
        },
      },
    });
  } catch (error) {
    console.error('Error getDashboardData:', error);
    return res.status(500).json({
      status: 'error',
      message: 'Gagal memuat data dashboard',
    });
  }
};

module.exports = { getDashboardData };