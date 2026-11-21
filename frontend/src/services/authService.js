import { USE_MOCK, apiRequest } from './apiClient';
import { DEMO_ACCOUNTS } from '../config/constants';

const AUTH_STORAGE_KEY = 'rokkus_auth_user';

export const authService = {
  async login({ username, password }) {
    if (!username || !username.trim()) {
      throw new Error('Username wajib diisi');
    }
    if (!password || !password.trim()) {
      throw new Error('Password wajib diisi');
    }

    if (USE_MOCK) {
      // Latency simulation
      await new Promise((resolve) => setTimeout(resolve, 500));

      const cleanUser = username.trim().toLowerCase();
      const account = DEMO_ACCOUNTS.find((acc) => acc.username === cleanUser);

      if (!account || password.length < 4) {
        throw new Error('Username atau password salah. Silakan coba lagi.');
      }

      const userData = {
        username: account.username,
        name: account.name,
        role: account.role,
        title: account.title,
        token: `mock-token-${Date.now()}`,
      };

      localStorage.setItem(AUTH_STORAGE_KEY, JSON.stringify(userData));
      return userData;
    }

    // Real API mode
    const data = await apiRequest('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ username, password }),
    });

    localStorage.setItem(AUTH_STORAGE_KEY, JSON.stringify(data.user));
    if (data.token) {
      localStorage.setItem('rokkus_token', data.token);
    }
    return data.user;
  },

  async logout() {
    if (USE_MOCK) {
      await new Promise((resolve) => setTimeout(resolve, 200));
      localStorage.removeItem(AUTH_STORAGE_KEY);
      localStorage.removeItem('rokkus_token');
      return { success: true };
    }

    try {
      await apiRequest('/auth/logout', { method: 'POST' });
    } finally {
      localStorage.removeItem(AUTH_STORAGE_KEY);
      localStorage.removeItem('rokkus_token');
    }
    return { success: true };
  },

  getCurrentUser() {
    try {
      const stored = localStorage.getItem(AUTH_STORAGE_KEY);
      return stored ? JSON.parse(stored) : null;
    } catch {
      return null;
    }
  },
};
