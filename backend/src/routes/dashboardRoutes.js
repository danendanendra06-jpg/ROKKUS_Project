const express = require('express');
const router = express.Router();
const { getDashboardData } = require('../controllers/dashboardController');
const { authenticateToken, authorizeRoles } = require('../middlewares/authMiddleware');

router.get('/', authenticateToken, authorizeRoles('pengelola_stok', 'pemilik'), getDashboardData);

module.exports = router;