/**
 * Administration & Governance Service
 * Interfaces with admin metrics, user accounts management, and system audit logs.
 */
class AdminService {
  static async getMetrics() {
    return ApiService.get('/api/v1/admin/metrics');
  }

  static async getUsers() {
    return ApiService.get('/api/v1/admin/users');
  }

  static async createUser(userData) {
    return ApiService.post('/api/v1/admin/users', userData);
  }

  static async toggleUserStatus(userId) {
    return ApiService.patch(`/api/v1/admin/users/${userId}/status`);
  }

  static async getAuditLogs(page = 1, limit = 25) {
    return ApiService.get('/api/v1/admin/audit-logs', { page, limit });
  }
}

window.AdminService = AdminService;
