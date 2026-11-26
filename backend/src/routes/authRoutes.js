const express = require('express');
const router = express.Router();
const { login, getCurrentUser } = require('../controllers/authController');
const { authenticateToken } = require('../middlewares/authMiddleware');
const validate = require('../middlewares/validateMiddleware');
const { loginSchema } = require('../validations/schemas');

router.post('/login', validate(loginSchema), login);
router.get('/me', authenticateToken, getCurrentUser);

module.exports = router;