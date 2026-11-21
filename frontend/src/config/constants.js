export const LOW_STOCK_THRESHOLD = 50;

export const ROLES = {
  PENGELOLA: 'pengelola',
  PEMILIK: 'pemilik',
};

export const ROLE_LABELS = {
  [ROLES.PENGELOLA]: 'Manajer Stok',
  [ROLES.PEMILIK]: 'Pemilik',
};

export const MENU_CATEGORIES = {
  ROTI_MANIS: 'Roti Manis',
  ROTI_ASIN: 'Roti Asin',
  TAMBAHAN: 'Tambahan',
};

export const COOKING_METHODS = ['Kukus', 'Bakar'];

export const ENTRY_SESSIONS = ['Sesi 1', 'Sesi 2', 'Lainnya'];

export const TOPPING_STATUS = {
  AMAN: 'Aman',
  HAMPIR_HABIS: 'Hampir Habis',
  HABIS: 'Habis',
};

export const TOPPING_UNITS = ['pcs', 'toples', 'pack', 'kg'];

export const DEMO_ACCOUNTS = [
  { username: 'pengelola', role: 'pengelola', name: 'Budi Santoso', title: 'Manajer Stok' },
  { username: 'pemilik', role: 'pemilik', name: 'Arif', title: 'Pemilik' },
];
