const Joi = require('joi');

const loginSchema = Joi.object({
  username: Joi.string().trim().required().messages({
    'string.empty': 'Username wajib diisi',
    'any.required': 'Username wajib diisi',
  }),
  password: Joi.string().required().messages({
    'string.empty': 'Password wajib diisi',
    'any.required': 'Password wajib diisi',
  }),
});

const createStockSchema = Joi.object({
  nama_barang: Joi.string().trim().min(2).max(100).required().messages({
    'string.empty': 'Nama barang wajib diisi',
    'any.required': 'Nama barang wajib diisi',
  }),
  kategori: Joi.string().trim().min(2).max(50).required().messages({
    'string.empty': 'Kategori wajib diisi',
    'any.required': 'Kategori wajib diisi',
  }),
  satuan: Joi.string().trim().min(1).max(20).required().messages({
    'string.empty': 'Satuan wajib diisi',
    'any.required': 'Satuan wajib diisi',
  }),
  stok_awal: Joi.number().integer().min(0).required().messages({
    'number.base': 'Stok awal harus berupa angka',
    'number.min': 'Stok awal tidak boleh negatif',
    'any.required': 'Stok awal wajib diisi',
  }),
  batas_minimum: Joi.number().integer().min(0).default(10).messages({
    'number.min': 'Batas minimum tidak boleh negatif',
  }),
});

const updateStockSchema = Joi.object({
  nama_barang: Joi.string().trim().min(2).max(100),
  kategori: Joi.string().trim().min(2).max(50),
  satuan: Joi.string().trim().min(1).max(20),
  stok_awal: Joi.number().integer().min(0),
  stok_terkini: Joi.number().integer().min(0),
  batas_minimum: Joi.number().integer().min(0),
}).min(1).messages({
  'object.min': 'Minimal satu field harus diisi untuk memperbarui data barang',
});

const createTransactionSchema = Joi.object({
  item_id: Joi.number().integer().positive().required().messages({
    'number.base': 'ID barang harus berupa angka',
    'any.required': 'Barang wajib dipilih',
  }),
  tipe_transaksi: Joi.string().valid('masuk', 'keluar').required().messages({
    'any.only': 'Tipe transaksi harus bernilai "masuk" atau "keluar"',
    'any.required': 'Tipe transaksi wajib diisi',
  }),
  jumlah: Joi.number().integer().min(1).required().messages({
    'number.base': 'Jumlah harus berupa angka bulat',
    'number.min': 'Jumlah transaksi minimal 1',
    'any.required': 'Jumlah transaksi wajib diisi',
  }),
  catatan: Joi.string().trim().max(255).allow('', null).default(''),
});

module.exports = {
  loginSchema,
  createStockSchema,
  updateStockSchema,
  createTransactionSchema,
};