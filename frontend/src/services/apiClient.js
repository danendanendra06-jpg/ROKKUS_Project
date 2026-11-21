const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:5000/api';
export const USE_MOCK = import.meta.env.VITE_USE_MOCK !== 'false';

/**
 * Dev simulation checks via URL parameters
 */
export function shouldSimulateLoadFail() {
  if (typeof window !== 'undefined') {
    return new URLSearchParams(window.location.search).get('simulateLoadFail') === '1';
  }
  return false;
}

export function shouldSimulateSaveFail() {
  if (typeof window !== 'undefined') {
    return new URLSearchParams(window.location.search).get('simulateSaveFail') === '1';
  }
  return false;
}

export function shouldSimulateAiFail() {
  if (typeof window !== 'undefined') {
    return new URLSearchParams(window.location.search).get('simulateAiFail') === '1';
  }
  return false;
}

/**
 * Common fetch helper for real REST API calls
 */
export async function apiRequest(endpoint, options = {}) {
  // Check simulation switches even in real API mode
  if (shouldSimulateLoadFail() && (!options.method || options.method === 'GET')) {
    throw new Error('Gagal memuat data. Periksa koneksi lalu coba lagi.');
  }

  if (shouldSimulateSaveFail() && (options.method === 'POST' || options.method === 'PUT' || options.method === 'PATCH')) {
    throw new Error('Transaksi gagal disimpan. Silakan coba lagi.');
  }

  const token = localStorage.getItem('rokkus_token');
  const headers = {
    'Content-Type': 'application/json',
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
    ...options.headers,
  };

  const response = await fetch(`${API_BASE_URL}${endpoint}`, {
    ...options,
    headers,
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    const error = new Error(errorData.message || 'Terjadi kesalahan pada server');
    error.status = response.status;
    error.data = errorData;
    throw error;
  }

  return response.json();
}
