import { USE_MOCK, apiRequest } from './apiClient';
import { mockStore } from './mockStore';

export const stockService = {
  async getBreadStock() {
    if (USE_MOCK) {
      return mockStore.getBreadStock();
    }
    return apiRequest('/stock/bread');
  },

  async updateInitialStock(quantity) {
    if (USE_MOCK) {
      return mockStore.updateInitialStock(quantity);
    }
    return apiRequest('/stock/bread/initial', {
      method: 'PATCH',
      body: JSON.stringify({ initialStock: quantity }),
    });
  },
};
