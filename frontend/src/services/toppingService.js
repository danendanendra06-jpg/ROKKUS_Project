import { USE_MOCK, apiRequest } from './apiClient';
import { mockStore } from './mockStore';

export const toppingService = {
  async getToppings() {
    if (USE_MOCK) {
      return mockStore.getToppings();
    }
    return apiRequest('/toppings');
  },

  async updateToppingStatus(id, status) {
    if (USE_MOCK) {
      return mockStore.updateToppingStatus(id, status);
    }
    return apiRequest(`/toppings/${id}/status`, {
      method: 'PATCH',
      body: JSON.stringify({ status }),
    });
  },

  async createToppingPurchase(payload) {
    if (USE_MOCK) {
      return mockStore.createToppingPurchase(payload);
    }
    return apiRequest('/topping-purchases', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  },

  async getToppingPurchases() {
    if (USE_MOCK) {
      return mockStore.getAllToppingPurchases();
    }
    return apiRequest('/topping-purchases');
  },
};
