const jwt = require('jsonwebtoken');

const authenticateToken = (req, res, next) => {
  const authHeader = req.headers['authorization'];
  const token = authHeader && authHeader.split(' ')[1]; // Format: Bearer <token>

  if (!token) {
    return res.status(401).json({
      status: 'fail',
      message: 'Akses ditolak. Silakan login terlebih dahulu.',
    });
  }

  try {
    const decoded = jwt.verify(token, process.env.JWT_SECRET);
    req.user = decoded;
    next();
  } catch (error) {
    return res.status(401).json({
      status: 'fail',
      message: 'Token tidak valid atau sudah kedaluwarsa.',
    });
  }
};

const authorizeRoles = (...allowedRoles) => (req, res, next) => {
  if (!req.user || !allowedRoles.includes(req.user.role)) {
    return res.status(403).json({
      status: 'fail',
      message: 'Anda tidak memiliki hak akses untuk melakukan tindakan ini.',
    });
  }
  next();
};

module.exports = { authenticateToken, authorizeRoles };