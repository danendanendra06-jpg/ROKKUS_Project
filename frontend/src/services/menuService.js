import { USE_MOCK, apiRequest } from './apiClient';
import { mockStore } from './mockStore';

export const menuService = {
  async getMenuItems(category) {
    if (USE_MOCK) {
      return mockStore.getMenuItems(category);
    }
    const query = category && category !== 'Semua' ? `?category=${encodeURIComponent(category)}` : '';
    return apiRequest(`/menu-items${query}`);
  },

  async createMenuItem(itemData) {
    if (USE_MOCK) {
      return mockStore.createMenuItem(itemData);
    }
    return apiRequest('/menu-items', {
      method: 'POST',
      body: JSON.stringify(itemData),
    });
  },

  async updateMenuItem(id, itemData) {
    if (USE_MOCK) {
      return mockStore.updateMenuItem(id, itemData);
    }
    return apiRequest(`/menu-items/${id}`, {
      method: 'PUT',
      body: JSON.stringify(itemData),
    });
  },

  async deleteMenuItem(id) {
    if (USE_MOCK) {
      return mockStore.deleteMenuItem(id);
    }
    return apiRequest(`/menu-items/${id}`, {
      method: 'DELETE',
    });
  },
};
