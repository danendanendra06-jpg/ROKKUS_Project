import { USE_MOCK, apiRequest } from './apiClient';
import { mockStore } from './mockStore';

export const dashboardService = {
  async getSummary() {
    if (USE_MOCK) {
      return mockStore.getDashboardSummary();
    }
    return apiRequest('/dashboard/summary');
  },

  async getAiSummary(shouldFail = false) {
    if (USE_MOCK) {
      return mockStore.getAiSummary(shouldFail);
    }
    const query = shouldFail ? '?simulateAiFail=1' : '';
    return apiRequest(`/dashboard/ai-summary${query}`);
  },
};
