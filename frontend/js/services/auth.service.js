/**
 * Authentication & Identity Service
 * Manages JWT tokens, authenticated profile, RBAC checks, and session persistence.
 */
class AuthService {
  static currentUser = null;
  static listeners = [];

  static subscribe(fn) {
    this.listeners.push(fn);
    return () => {
      this.listeners = this.listeners.filter(l => l !== fn);
    };
  }

  static notify() {
    this.listeners.forEach(fn => fn(this.currentUser));
  }

  static async init() {
    let token = ApiService.getAuthToken();
    const storedUser = localStorage.getItem('upay_shield_user');
    if (storedUser) {
      try {
        this.currentUser = JSON.parse(storedUser);
      } catch (e) {
        this.currentUser = null;
      }
    }

    if (token) {
      try {
        const res = await ApiService.get('/api/v1/auth/me');
        if (res && res.data) {
          this.currentUser = res.data;
          localStorage.setItem('upay_shield_user', JSON.stringify(this.currentUser));
          this.notify();
          return this.currentUser;
        }
      } catch (err) {
        console.warn('[AuthService] Stored token expired or invalid, refreshing session...');
        ApiService.setAuthToken(null);
        token = null;
      }
    }

    // Auto-authenticate with demo admin credentials if no valid session token exists
    if (!token) {
      try {
        const loginRes = await ApiService.post('/api/v1/auth/login', {
          username_or_email: 'admin',
          password: 'Admin@1234'
        });
        if (loginRes && loginRes.data && loginRes.data.access_token) {
          ApiService.setAuthToken(loginRes.data.access_token);
          this.currentUser = loginRes.data.user;
          localStorage.setItem('upay_shield_user', JSON.stringify(this.currentUser));
        }
      } catch (e) {
        console.warn('[AuthService] Automatic demo login note:', e.message);
        if (!this.currentUser) {
          this.currentUser = {
            username: 'admin',
            full_name: 'System Administrator',
            role: 'ADMIN',
            department: 'Information Security & Risk Management',
            is_active: true
          };
        }
      }
    }

    this.notify();
    return this.currentUser;
  }

  static async login(username_or_email, password) {
    const res = await ApiService.post('/api/v1/auth/login', {
      username_or_email,
      password
    });

    if (res && res.data && res.data.access_token) {
      ApiService.setAuthToken(res.data.access_token);
      this.currentUser = res.data.user;
      localStorage.setItem('upay_shield_user', JSON.stringify(this.currentUser));
      this.notify();
      return this.currentUser;
    }
    throw new Error('Invalid login response from server.');
  }

  static async register(data) {
    const res = await ApiService.post('/api/v1/auth/register', data);
    return res;
  }

  static logout() {
    ApiService.setAuthToken(null);
    localStorage.removeItem('upay_shield_user');
    this.currentUser = {
      username: 'guest',
      full_name: 'Guest Officer',
      role: 'VIEWER',
      department: 'Guest Access Desk',
      is_active: true
    };
    this.notify();
  }

  static getCurrentUser() {
    return this.currentUser;
  }

  static hasRole(requiredRoles) {
    if (!this.currentUser) return false;
    if (typeof requiredRoles === 'string') {
      return this.currentUser.role === requiredRoles;
    }
    return requiredRoles.includes(this.currentUser.role);
  }

  static isAdmin() {
    return this.hasRole('ADMIN');
  }

  static isSeniorOfficer() {
    return this.hasRole(['ADMIN', 'SENIOR_OFFICER']);
  }
}

window.AuthService = AuthService;
