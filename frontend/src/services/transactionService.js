import { USE_MOCK, apiRequest } from './apiClient';
import { mockStore } from './mockStore';

export const transactionService = {
  async getTransactions(filters = {}) {
    if (USE_MOCK) {
      return mockStore.getTransactions(filters);
    }
    const params = new URLSearchParams();
    if (filters.from) params.append('from', filters.from);
    if (filters.to) params.append('to', filters.to);
    if (filters.type && filters.type !== 'Semua') params.append('type', filters.type);
    if (filters.q) params.append('q', filters.q);
    if (filters.page) params.append('page', filters.page);
    if (filters.limit) params.append('limit', filters.limit);

    return apiRequest(`/transactions?${params.toString()}`);
  },

  async createTransaction(payload) {
    if (USE_MOCK) {
      return mockStore.createTransaction(payload);
    }
    return apiRequest('/transactions', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  },
};
