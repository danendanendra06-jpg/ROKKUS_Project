const axios = require('axios');
const pool = require('../config/db');

// Helper pembulatan 2 angka desimal agar payload rapi & bebas NaN/Infinity
const round2 = (num) => Math.round((Number(num) || 0) * 100) / 100;

const getDashboardData = async (req, res) => {
  try {
    const stocksResult = await pool.query(`
      SELECT 
        i.id,
        i.nama_barang,
        i.kategori,
        i.satuan,
        i.stok_awal,
        i.stok_terkini,
        i.batas_minimum,
        CASE 
          WHEN i.stok_terkini = 0 THEN 'habis'
          WHEN i.stok_terkini <= i.batas_minimum THEN 'menipis'
          ELSE 'aman'
        END AS status_dasar,
        i.updated_at,
        COALESCE(SUM(CASE WHEN t.tipe_transaksi = 'masuk' AND t.created_at >= CURRENT_DATE THEN t.jumlah ELSE 0 END), 0) AS barang_masuk_hari_ini,
        COALESCE(SUM(CASE WHEN t.tipe_transaksi = 'keluar' AND t.created_at >= CURRENT_DATE THEN t.jumlah ELSE 0 END), 0) AS barang_keluar_hari_ini,
        COALESCE(SUM(CASE WHEN t.tipe_transaksi = 'masuk' AND t.created_at >= CURRENT_DATE - INTERVAL '6 days' THEN t.jumlah ELSE 0 END), 0) AS total_masuk_7h,
        COALESCE(SUM(CASE WHEN t.tipe_transaksi = 'keluar' AND t.created_at >= CURRENT_DATE - INTERVAL '6 days' THEN t.jumlah ELSE 0 END), 0) AS total_keluar_7h
      FROM items i
      LEFT JOIN stock_transactions t ON t.item_id = i.id
      GROUP BY i.id
      ORDER BY i.id ASC
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

    const rawItems = stocksResult.rows;
    const recentTransactions = recentTrxResult.rows;

    const items = rawItems.map((row) => ({
      id: row.id,
      nama_barang: row.nama_barang,
      kategori: row.kategori,
      satuan: row.satuan,
      stok_awal: row.stok_awal,
      stok_terkini: row.stok_terkini,
      batas_minimum: row.batas_minimum,
      status_dasar: row.status_dasar,
      updated_at: row.updated_at,
    }));

    const ringkasanStok = {
      total_barang: items.length,
      stok_aman: items.filter((i) => i.status_dasar === 'aman').length,
      stok_menipis: items.filter((i) => i.status_dasar === 'menipis').length,
      stok_habis: items.filter((i) => i.status_dasar === 'habis').length,
    };

    const mlPayloadItems = rawItems.map((row) => {
      const stokSaatIni = Math.max(0, Number(row.stok_terkini) || 0);
      const batasMinimum = Math.max(0, Number(row.batas_minimum) || 0);
      const barangMasuk = Math.max(0, Number(row.barang_masuk_hari_ini) || 0);
      const barangKeluar = Math.max(0, Number(row.barang_keluar_hari_ini) || 0);
      const totalMasuk7h = Math.max(0, Number(row.total_masuk_7h) || 0);
      const totalKeluar7h = Math.max(0, Number(row.total_keluar_7h) || 0);
      const avgKeluar7h = round2(totalKeluar7h / 7);

      let daysOfCover = 0;
      if (stokSaatIni > 0) {
        daysOfCover = avgKeluar7h > 0 ? Math.min(30, round2(stokSaatIni / avgKeluar7h)) : 30;
      }

      let rasioStok = 0;
      if (batasMinimum > 0) {
        rasioStok = round2(stokSaatIni / batasMinimum);
      } else if (stokSaatIni > 0) {
        rasioStok = round2(stokSaatIni);
      }

      return {
        stok_saat_ini: stokSaatIni,
        batas_minimum: batasMinimum,
        barang_masuk: barangMasuk,
        barang_keluar: barangKeluar,
        avg_keluar_7h: avgKeluar7h,
        days_of_cover: daysOfCover,
        rasio_stok: rasioStok,
        total_masuk_7h: totalMasuk7h,
        total_keluar_7h: totalKeluar7h,
        kategori: row.kategori && row.kategori.trim() ? row.kategori.trim() : 'roti_kukus',
        rasa: row.nama_barang && row.nama_barang.trim() ? row.nama_barang.trim() : 'original',
      };
    });

    let aiClassification = null;
    let aiSummary = null;
    let mlAvailable = false;
    let genAiAvailable = false;

    const mlApiUrl = process.env.ML_API_URL;
    const genAiApiUrl = process.env.GENAI_API_URL;

    const mlPromise =
      mlApiUrl && mlPayloadItems.length > 0
        ? axios.post(
            `${mlApiUrl}/ml/predict-status`,
            { items: mlPayloadItems },
            { timeout: 5000 }
          )
        : Promise.reject(
            new Error(
              !mlApiUrl
                ? 'ML_API_URL belum dikonfigurasi'
                : 'Belum ada data barang untuk diprediksi'
            )
          );

    const genAiPromise = genAiApiUrl
      ? axios.post(
          `${genAiApiUrl}/api/v1/summary/daily`,
          {
            items,
            recent_transactions: recentTransactions,
            ringkasan_stok: ringkasanStok,
          },
          { timeout: 8000 }
        )
      : Promise.reject(new Error('GENAI_API_URL belum dikonfigurasi'));

    const [mlResult, genAiResult] = await Promise.allSettled([mlPromise, genAiPromise]);

    if (mlResult.status === 'fulfilled') {
      mlAvailable = true;
      const mlData = mlResult.value.data;

      const prediksiTerpetakan = Array.isArray(mlData?.prediksi)
        ? mlData.prediksi.map((pred, idx) => ({
            item_id: items[idx]?.id ?? null,
            nama_barang: items[idx]?.nama_barang ?? null,
            status: pred.status,
            probabilitas: pred.probabilitas,
            versi_model: pred.versi_model,
          }))
        : [];

      aiClassification = {
        total_items: mlData?.total_items ?? prediksiTerpetakan.length,
        prediksi: prediksiTerpetakan,
      };
    } else if (mlApiUrl && mlPayloadItems.length > 0) {
      console.warn(
        'Layanan ML tidak dapat diakses:',
        mlResult.reason?.response?.data || mlResult.reason?.message
      );
    }

    if (genAiResult.status === 'fulfilled') {
      genAiAvailable = true;
      const genData = genAiResult.value.data;
      aiSummary =
        genData?.summary ||
        genData?.ringkasan ||
        genData?.daily_summary ||
        genData?.data?.summary ||
        genData?.data?.ringkasan ||
        (typeof genData === 'string' ? genData : null);

      if (aiSummary) {
        await pool.query(
          'INSERT INTO ai_summaries (ringkasan, sumber) VALUES ($1, $2)',
          [aiSummary, 'generative_ai']
        );
      }
    } else if (genAiApiUrl) {
      console.warn(
        'Layanan GenAI tidak dapat diakses:',
        genAiResult.reason?.response?.data || genAiResult.reason?.message
      );
    }

    let aiStatus = 'unavailable';
    let aiMessage = 'Layanan AI tidak tersedia';

    if (mlAvailable && genAiAvailable) {
      aiStatus = 'available';
      aiMessage = 'Layanan ML dan GenAI aktif';
    } else if (mlAvailable) {
      aiStatus = 'partial';
      aiMessage = 'Layanan ML aktif, layanan GenAI tidak tersedia';
    } else if (genAiAvailable) {
      aiStatus = 'partial';
      aiMessage = 'Layanan GenAI aktif, layanan ML tidak tersedia';
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