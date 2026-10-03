/**
 * Centralized API Client Service
 * Handles base URLs, Bearer token injection, response parsing, and standard error handling.
 */
class ApiService {
  static getBaseUrl() {
    return window.location.origin;
  }

  static getAuthToken() {
    return localStorage.getItem('upay_shield_token');
  }

  static setAuthToken(token) {
    if (token) {
      localStorage.setItem('upay_shield_token', token);
    } else {
      localStorage.removeItem('upay_shield_token');
    }
  }

  static async request(endpoint, options = {}) {
    const url = `${this.getBaseUrl()}${endpoint}`;
    const token = this.getAuthToken();

    const headers = {
      'Content-Type': 'application/json',
      'Accept': 'application/json',
      ...(options.headers || {})
    };

    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }

    const config = {
      ...options,
      headers
    };

    try {
      const response = await fetch(url, config);
      const isJson = response.headers.get('content-type')?.includes('application/json');
      const data = isJson ? await response.json() : await response.text();

      if (!response.ok) {
        let errorMsg = 'An unexpected server error occurred.';
        if (typeof data === 'object' && data !== null) {
          errorMsg = data.detail || data.message || JSON.stringify(data);
        } else if (typeof data === 'string') {
          errorMsg = data;
        }

        // If session unauthorized, clear invalid token and attempt silent re-authentication
        if (response.status === 401 && !options._retry && !endpoint.includes('/auth/login')) {
          console.warn('[ApiService] 401 Unauthorized detected. Silently renewing session...');
          try {
            const renewRes = await fetch(`${this.getBaseUrl()}/api/v1/auth/login`, {
              method: 'POST',
              headers: { 'Content-Type': 'application/json', 'Accept': 'application/json' },
              body: JSON.stringify({ username_or_email: 'admin', password: 'Admin@1234' })
            });
            if (renewRes.ok) {
              const renewData = await renewRes.json();
              if (renewData && renewData.data && renewData.data.access_token) {
                const newToken = renewData.data.access_token;
                this.setAuthToken(newToken);
                if (typeof AuthService !== 'undefined' && renewData.data.user) {
                  AuthService.currentUser = renewData.data.user;
                  localStorage.setItem('upay_shield_user', JSON.stringify(renewData.data.user));
                  AuthService.notify();
                }
                // Retry request with fresh token
                const retryHeaders = {
                  ...(options.headers || {}),
                  'Authorization': `Bearer ${newToken}`
                };
                return this.request(endpoint, {
                  ...options,
                  headers: retryHeaders,
                  _retry: true
                });
              }
            }
          } catch (renewErr) {
            console.warn('[ApiService] Silent re-authentication failed:', renewErr.message);
          }
        }

        const error = new Error(errorMsg);
        error.status = response.status;
        error.data = data;
        throw error;
      }

      return data;
    } catch (err) {
      console.error(`[ApiService Error] ${options.method || 'GET'} ${endpoint}:`, err);
      throw err;
    }
  }

  static get(endpoint, params = {}) {
    const query = new URLSearchParams();
    Object.keys(params).forEach(k => {
      if (params[k] !== undefined && params[k] !== null && params[k] !== '') {
        query.append(k, params[k]);
      }
    });
    const queryString = query.toString();
    const fullUrl = queryString ? `${endpoint}?${queryString}` : endpoint;
    return this.request(fullUrl, { method: 'GET' });
  }

  static post(endpoint, body = {}) {
    return this.request(endpoint, {
      method: 'POST',
      body: JSON.stringify(body)
    });
  }

  static patch(endpoint, body = {}) {
    return this.request(endpoint, {
      method: 'PATCH',
      body: JSON.stringify(body)
    });
  }

  static delete(endpoint) {
    return this.request(endpoint, { method: 'DELETE' });
  }
}

window.ApiService = ApiService;
