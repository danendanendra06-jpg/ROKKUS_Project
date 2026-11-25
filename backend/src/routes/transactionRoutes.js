const express = require('express');
const router = express.Router();
const { getAllTransactions, createTransaction } = require('../controllers/transactionController');
const { authenticateToken, authorizeRoles } = require('../middlewares/authMiddleware');
const validate = require('../middlewares/validateMiddleware');
const { createTransactionSchema } = require('../validations/schemas');

router.get(
  '/',
  authenticateToken,
  authorizeRoles('pengelola_stok', 'pemilik'),
  getAllTransactions
);

router.post(
  '/',
  authenticateToken,
  authorizeRoles('pengelola_stok'),
  validate(createTransactionSchema),
  createTransaction
);

module.exports = router;