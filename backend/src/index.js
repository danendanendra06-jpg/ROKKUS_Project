const express = require('express');
const cors = require('cors');
require('dotenv').config();

const authRoutes = require('./routes/authRoutes');
const stockRoutes = require('./routes/stockRoutes');
const transactionRoutes = require('./routes/transactionRoutes');
const dashboardRoutes = require('./routes/dashboardRoutes');

const app = express();
const PORT = process.env.PORT || 5000;

app.use(cors());
app.use(express.json());

// Health check
app.get('/api/v1/health', (req, res) => {
  res.status(200).json({ status: 'success', message: 'Backend ROKKUS aktif' });
});

// Daftarkan seluruh endpoint API v1
app.use('/api/v1/auth', authRoutes);
app.use('/api/v1/stocks', stockRoutes);
app.use('/api/v1/transactions', transactionRoutes);
app.use('/api/v1/dashboard', dashboardRoutes);

// Handler 404 untuk route tidak dikenal
app.use((req, res) => {
  res.status(404).json({
    status: 'fail',
    message: 'Endpoint tidak ditemukan',
  });
});

// Global Error Handler
app.use((err, req, res, next) => {
  console.error('Unhandled Error:', err);
  res.status(500).json({
    status: 'error',
    message: 'Terjadi kesalahan internal pada server',
  });
});

app.listen(PORT, () => {
  console.log(`Server berjalan di http://localhost:${PORT}`);
});