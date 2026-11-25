const bcrypt = require('bcryptjs');
const pool = require('../src/config/db');

const seedUsers = async () => {
  try {
    const pengelolaHash = await bcrypt.hash('pengelola123', 10);
    const pemilikHash = await bcrypt.hash('pemilik123', 10);

    await pool.query(
      `INSERT INTO users (nama, username, password_hash, role)
       VALUES 
         ('Manajer Stok ROKKUS', 'pengelola', $1, 'pengelola_stok'),
         ('Pemilik ROKKUS', 'pemilik', $2, 'pemilik')
       ON CONFLICT (username) DO NOTHING`,
      [pengelolaHash, pemilikHash]
    );

    console.log('Akun demo berhasil dibuat:');
    console.log('- Pengelola Stok -> username: pengelola | password: pengelola123');
    console.log('- Pemilik        -> username: pemilik   | password: pemilik123');
  } catch (error) {
    console.error('Gagal seeding users:', error);
  } finally {
    await pool.end();
  }
};

seedUsers();