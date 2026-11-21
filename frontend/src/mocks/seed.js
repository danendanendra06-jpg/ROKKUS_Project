import { getTodayDateString } from '../utils/date';

const today = getTodayDateString();

// Helper to calculate past dates (YYYY-MM-DD)
function getPastDate(daysAgo) {
  const d = new Date();
  d.setDate(d.getDate() - daysAgo);
  const year = d.getFullYear();
  const month = String(d.getMonth() + 1).padStart(2, '0');
  const day = String(d.getDate()).padStart(2, '0');
  return `${year}-${month}-${day}`;
}

export const initialBreadStock = {
  name: "Roti Hijau Pandan",
  unit: "pcs",
  stock: 45,
  initialStock: 0,
  masukHariIni: 100,
  keluarHariIni: 55,
  updatedAt: `${today} 16:45`,
};

export const initialMenuItems = [
  // Roti Manis
  { id: 'm-1', name: 'Lotus Biscoff', category: 'Roti Manis', tag: 'Baru', todaySales: 2 },
  { id: 'm-2', name: 'Coklat Keju', category: 'Roti Manis', tag: 'Best Seller', todaySales: 10 },
  { id: 'm-3', name: 'Coklat Kacang', category: 'Roti Manis', tag: null, todaySales: 3 },
  { id: 'm-4', name: 'Nutella Keju', category: 'Roti Manis', tag: 'Best Seller', todaySales: 7 },
  { id: 'm-5', name: 'Silverqueen Keju', category: 'Roti Manis', tag: null, todaySales: 2 },
  { id: 'm-6', name: 'Ovomaltine Keju', category: 'Roti Manis', tag: 'Best Seller', todaySales: 4 },
  { id: 'm-7', name: 'Srikaya', category: 'Roti Manis', tag: 'Best Seller', todaySales: 2 },
  { id: 'm-8', name: 'Coklat Crunchy', category: 'Roti Manis', tag: 'Best Seller', todaySales: 14 },
  { id: 'm-9', name: 'Keju', category: 'Roti Manis', tag: null, todaySales: 0 },
  { id: 'm-10', name: 'Strawberry', category: 'Roti Manis', tag: null, todaySales: 0 },
  { id: 'm-11', name: 'Blueberry', category: 'Roti Manis', tag: null, todaySales: 0 },
  { id: 'm-12', name: 'Tiramisu', category: 'Roti Manis', tag: null, todaySales: 0 },
  { id: 'm-13', name: 'Greentea', category: 'Roti Manis', tag: null, todaySales: 0 },
  { id: 'm-14', name: 'Kacang (Peanut Butter)', category: 'Roti Manis', tag: null, todaySales: 0 },
  { id: 'm-15', name: 'Nutella', category: 'Roti Manis', tag: null, todaySales: 0 },
  { id: 'm-16', name: 'Silverqueen', category: 'Roti Manis', tag: null, todaySales: 0 },
  { id: 'm-17', name: 'Ovomaltine', category: 'Roti Manis', tag: null, todaySales: 0 },

  // Roti Asin
  { id: 'm-18', name: 'Telur Mayo', category: 'Roti Asin', tag: 'Best Seller', todaySales: 6 },
  { id: 'm-19', name: 'Sosis Mayo', category: 'Roti Asin', tag: null, todaySales: 0 },
  { id: 'm-20', name: 'Telur Sosis Mayo', category: 'Roti Asin', tag: null, todaySales: 0 },
  { id: 'm-21', name: 'Beef Mayo', category: 'Roti Asin', tag: 'Best Seller', todaySales: 5 },
  { id: 'm-22', name: 'Beef Sosis Mayo', category: 'Roti Asin', tag: null, todaySales: 0 },
  { id: 'm-23', name: 'Telur Beef', category: 'Roti Asin', tag: null, todaySales: 0 },
  { id: 'm-24', name: 'Double Beef', category: 'Roti Asin', tag: null, todaySales: 0 },
  { id: 'm-25', name: 'Telur Beef Sosis', category: 'Roti Asin', tag: 'Best Seller', todaySales: 0 },

  // Tambahan
  { id: 'm-26', name: 'Keju Slice', category: 'Tambahan', tag: 'Baru', todaySales: 3 },
  { id: 'm-27', name: 'Keju Parut', category: 'Tambahan', tag: 'Best Seller', todaySales: 8 },
  { id: 'm-28', name: 'Telur', category: 'Tambahan', tag: null, todaySales: 2 },
  { id: 'm-29', name: 'Selai Lain', category: 'Tambahan', tag: null, todaySales: 1 },
];

export const initialToppings = [
  {
    id: 'top-1',
    name: 'Coklat',
    status: 'Aman',
    purchases: [
      { id: 'tp-101', date: getPastDate(15), qty: 5, unit: 'kg', recordedBy: 'Budi Santoso' },
      { id: 'tp-102', date: getPastDate(7), qty: 5, unit: 'kg', recordedBy: 'Budi Santoso' },
      { id: 'tp-103', date: getPastDate(1), qty: 5, unit: 'kg', recordedBy: 'Budi Santoso' },
    ]
  },
  {
    id: 'top-2',
    name: 'Keju Parut',
    status: 'Hampir Habis',
    purchases: [
      { id: 'tp-201', date: getPastDate(12), qty: 4, unit: 'kg', recordedBy: 'Budi Santoso' },
      { id: 'tp-202', date: getPastDate(4), qty: 4, unit: 'kg', recordedBy: 'Budi Santoso' },
    ]
  },
  {
    id: 'top-3',
    name: 'Keju Slice',
    status: 'Aman',
    purchases: [
      { id: 'tp-301', date: getPastDate(18), qty: 6, unit: 'pack', recordedBy: 'Budi Santoso' },
      { id: 'tp-302', date: getPastDate(9), qty: 6, unit: 'pack', recordedBy: 'Budi Santoso' },
      { id: 'tp-303', date: getPastDate(2), qty: 6, unit: 'pack', recordedBy: 'Budi Santoso' },
    ]
  },
  {
    id: 'top-4',
    name: 'Nutella',
    status: 'Habis',
    purchases: [
      { id: 'tp-401', date: getPastDate(20), qty: 3, unit: 'toples', recordedBy: 'Budi Santoso' },
      { id: 'tp-402', date: getPastDate(8), qty: 2, unit: 'toples', recordedBy: 'Budi Santoso' },
    ]
  },
  {
    id: 'top-5',
    name: 'Silverqueen',
    status: 'Aman',
    purchases: [
      { id: 'tp-501', date: getPastDate(14), qty: 10, unit: 'pcs', recordedBy: 'Budi Santoso' },
      { id: 'tp-502', date: getPastDate(5), qty: 10, unit: 'pcs', recordedBy: 'Budi Santoso' },
    ]
  },
  {
    id: 'top-6',
    name: 'Ovomaltine',
    status: 'Hampir Habis',
    purchases: [
      { id: 'tp-601', date: getPastDate(16), qty: 3, unit: 'toples', recordedBy: 'Budi Santoso' },
      { id: 'tp-602', date: getPastDate(6), qty: 3, unit: 'toples', recordedBy: 'Budi Santoso' },
    ]
  },
  {
    id: 'top-7',
    name: 'Lotus Biscoff',
    status: 'Aman',
    purchases: [
      { id: 'tp-701', date: getPastDate(3), qty: 4, unit: 'toples', recordedBy: 'Budi Santoso' },
    ]
  },
  {
    id: 'top-8',
    name: 'Selai Kacang',
    status: 'Aman',
    purchases: [
      { id: 'tp-801', date: getPastDate(21), qty: 3, unit: 'kg', recordedBy: 'Budi Santoso' },
      { id: 'tp-802', date: getPastDate(10), qty: 3, unit: 'kg', recordedBy: 'Budi Santoso' },
    ]
  },
  {
    id: 'top-9',
    name: 'Srikaya',
    status: 'Hampir Habis',
    purchases: [
      { id: 'tp-901', date: getPastDate(14), qty: 2, unit: 'toples', recordedBy: 'Budi Santoso' },
      { id: 'tp-902', date: getPastDate(5), qty: 2, unit: 'toples', recordedBy: 'Budi Santoso' },
    ]
  },
  {
    id: 'top-10',
    name: 'Telur',
    status: 'Aman',
    purchases: [
      { id: 'tp-1001', date: getPastDate(12), qty: 5, unit: 'kg', recordedBy: 'Budi Santoso' },
      { id: 'tp-1002', date: getPastDate(6), qty: 5, unit: 'kg', recordedBy: 'Budi Santoso' },
      { id: 'tp-1003', date: getPastDate(1), qty: 5, unit: 'kg', recordedBy: 'Budi Santoso' },
    ]
  },
  {
    id: 'top-11',
    name: 'Sosis',
    status: 'Aman',
    purchases: [
      { id: 'tp-1101', date: getPastDate(10), qty: 6, unit: 'pack', recordedBy: 'Budi Santoso' },
      { id: 'tp-1102', date: getPastDate(3), qty: 6, unit: 'pack', recordedBy: 'Budi Santoso' },
    ]
  },
  {
    id: 'top-12',
    name: 'Beef',
    status: 'Hampir Habis',
    purchases: [
      { id: 'tp-1201', date: getPastDate(11), qty: 5, unit: 'pack', recordedBy: 'Budi Santoso' },
      { id: 'tp-1202', date: getPastDate(4), qty: 5, unit: 'pack', recordedBy: 'Budi Santoso' },
    ]
  },
  {
    id: 'top-13',
    name: 'Mayo',
    status: 'Aman',
    purchases: [
      { id: 'tp-1301', date: getPastDate(14), qty: 4, unit: 'kg', recordedBy: 'Budi Santoso' },
      { id: 'tp-1302', date: getPastDate(7), qty: 4, unit: 'kg', recordedBy: 'Budi Santoso' },
    ]
  },
];

export const initialTransactions = [
  {
    id: 'trx-12',
    datetime: `${today} 16:30`,
    date: today,
    type: 'keluar',
    totalQty: 6,
    details: 'Coklat Crunchy 4, Telur Mayo 2',
    items: [
      { menuItemId: 'm-8', name: 'Coklat Crunchy', qty: 4, category: 'Roti Manis' },
      { menuItemId: 'm-18', name: 'Telur Mayo', qty: 2, category: 'Roti Asin' },
    ],
    cookingMethod: 'Kukus',
    stockAfter: 45,
    recordedBy: 'Budi Santoso',
    note: 'Pelanggan minta kukus hangat'
  },
  {
    id: 'trx-11',
    datetime: `${today} 15:45`,
    date: today,
    type: 'keluar',
    totalQty: 9,
    details: 'Coklat Keju 5, Nutella Keju 4, Keju Slice 2 (Tambahan)',
    items: [
      { menuItemId: 'm-2', name: 'Coklat Keju', qty: 5, category: 'Roti Manis' },
      { menuItemId: 'm-4', name: 'Nutella Keju', qty: 4, category: 'Roti Manis' },
      { menuItemId: 'm-26', name: 'Keju Slice', qty: 2, category: 'Tambahan' },
    ],
    cookingMethod: 'Bakar',
    stockAfter: 51,
    recordedBy: 'Budi Santoso',
    note: ''
  },
  {
    id: 'trx-10',
    datetime: `${today} 14:15`,
    date: today,
    type: 'keluar',
    totalQty: 8,
    details: 'Beef Mayo 5, Coklat Kacang 3',
    items: [
      { menuItemId: 'm-21', name: 'Beef Mayo', qty: 5, category: 'Roti Asin' },
      { menuItemId: 'm-3', name: 'Coklat Kacang', qty: 3, category: 'Roti Manis' },
    ],
    cookingMethod: 'Bakar',
    stockAfter: 60,
    recordedBy: 'Budi Santoso',
    note: ''
  },
  {
    id: 'trx-9',
    datetime: `${today} 13:30`,
    date: today,
    type: 'masuk',
    totalQty: 40,
    details: 'Sesi 2 - Pasokan Siang',
    session: 'Sesi 2',
    cookingMethod: '-',
    stockAfter: 68,
    recordedBy: 'Budi Santoso',
    note: 'Stok tambahan dari dapur pusat'
  },
  {
    id: 'trx-8',
    datetime: `${today} 12:20`,
    date: today,
    type: 'keluar',
    totalQty: 10,
    details: 'Coklat Crunchy 6, Telur Mayo 4',
    items: [
      { menuItemId: 'm-8', name: 'Coklat Crunchy', qty: 6, category: 'Roti Manis' },
      { menuItemId: 'm-18', name: 'Telur Mayo', qty: 4, category: 'Roti Asin' },
    ],
    cookingMethod: 'Kukus',
    stockAfter: 28,
    recordedBy: 'Budi Santoso',
    note: 'Ramai jam makan siang'
  },
  {
    id: 'trx-7',
    datetime: `${today} 11:10`,
    date: today,
    type: 'keluar',
    totalQty: 8,
    details: 'Coklat Keju 5, Nutella Keju 3',
    items: [
      { menuItemId: 'm-2', name: 'Coklat Keju', qty: 5, category: 'Roti Manis' },
      { menuItemId: 'm-4', name: 'Nutella Keju', qty: 3, category: 'Roti Manis' },
    ],
    cookingMethod: 'Bakar',
    stockAfter: 38,
    recordedBy: 'Budi Santoso',
    note: ''
  },
  {
    id: 'trx-6',
    datetime: `${today} 10:00`,
    date: today,
    type: 'keluar',
    totalQty: 6,
    details: 'Ovomaltine Keju 4, Silverqueen Keju 2',
    items: [
      { menuItemId: 'm-6', name: 'Ovomaltine Keju', qty: 4, category: 'Roti Manis' },
      { menuItemId: 'm-5', name: 'Silverqueen Keju', qty: 2, category: 'Roti Manis' },
    ],
    cookingMethod: 'Kukus',
    stockAfter: 46,
    recordedBy: 'Budi Santoso',
    note: ''
  },
  {
    id: 'trx-5',
    datetime: `${today} 09:15`,
    date: today,
    type: 'keluar',
    totalQty: 8,
    details: 'Coklat Crunchy 4, Lotus Biscoff 2, Srikaya 2',
    items: [
      { menuItemId: 'm-8', name: 'Coklat Crunchy', qty: 4, category: 'Roti Manis' },
      { menuItemId: 'm-1', name: 'Lotus Biscoff', qty: 2, category: 'Roti Manis' },
      { menuItemId: 'm-7', name: 'Srikaya', qty: 2, category: 'Roti Manis' },
    ],
    cookingMethod: 'Kukus',
    stockAfter: 52,
    recordedBy: 'Budi Santoso',
    note: ''
  },
  {
    id: 'trx-4',
    datetime: `${today} 08:00`,
    date: today,
    type: 'masuk',
    totalQty: 60,
    details: 'Sesi 1 - Pasokan Pagi Buka Outlet',
    session: 'Sesi 1',
    cookingMethod: '-',
    stockAfter: 60,
    recordedBy: 'Budi Santoso',
    note: 'Kondisi roti kukus pandan segar'
  },
  // Yesterday's transactions
  {
    id: 'trx-3',
    datetime: `${getPastDate(1)} 20:30`,
    date: getPastDate(1),
    type: 'keluar',
    totalQty: 12,
    details: 'Coklat Keju 6, Beef Mayo 6',
    items: [
      { menuItemId: 'm-2', name: 'Coklat Keju', qty: 6, category: 'Roti Manis' },
      { menuItemId: 'm-21', name: 'Beef Mayo', qty: 6, category: 'Roti Asin' },
    ],
    cookingMethod: 'Bakar',
    stockAfter: 8,
    recordedBy: 'Budi Santoso',
    note: 'Penutupan outlet malam'
  },
  {
    id: 'trx-2',
    datetime: `${getPastDate(1)} 14:00`,
    date: getPastDate(1),
    type: 'masuk',
    totalQty: 50,
    details: 'Sesi 2 - Pasokan Siang',
    session: 'Sesi 2',
    cookingMethod: '-',
    stockAfter: 72,
    recordedBy: 'Budi Santoso',
    note: ''
  },
  {
    id: 'trx-1',
    datetime: `${getPastDate(1)} 08:00`,
    date: getPastDate(1),
    type: 'masuk',
    totalQty: 70,
    details: 'Sesi 1 - Pasokan Pagi Buka Outlet',
    session: 'Sesi 1',
    cookingMethod: '-',
    stockAfter: 70,
    recordedBy: 'Budi Santoso',
    note: ''
  },
];
