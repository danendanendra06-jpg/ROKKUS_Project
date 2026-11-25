const express = require('express');
const router = express.Router();
const {
  getAllStocks,
  getStockById,
  createStock,
  updateStock,
  deleteStock,
} = require('../controllers/stockController');
const { authenticateToken, authorizeRoles } = require('../middlewares/authMiddleware');
const validate = require('../middlewares/validateMiddleware');
const { createStockSchema, updateStockSchema } = require('../validations/schemas');

router.get('/', authenticateToken, authorizeRoles('pengelola_stok', 'pemilik'), getAllStocks);
router.get('/:id', authenticateToken, authorizeRoles('pengelola_stok', 'pemilik'), getStockById);

router.post(
  '/',
  authenticateToken,
  authorizeRoles('pengelola_stok'),
  validate(createStockSchema),
  createStock
);

router.put(
  '/:id',
  authenticateToken,
  authorizeRoles('pengelola_stok'),
  validate(updateStockSchema),
  updateStock
);

router.delete('/:id', authenticateToken, authorizeRoles('pengelola_stok'), deleteStock);

module.exports = router;