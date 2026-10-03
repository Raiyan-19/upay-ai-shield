/**
 * Client-Side History PushState Router with Dynamic Component Mounting
 * Renders individual page views on demand from modular /views/*.html templates.
 */
class AppRouter {
  static routes = {
    '/': 'dashboard',
    '/dashboard': 'dashboard',
    '/transactions': 'transactions',
    '/cases': 'cases',
    '/simulator': 'simulator',
    '/behavior': 'behavior',
    '/scam': 'scam',
    '/network': 'network',
    '/model': 'model',
    '/monitoring': 'monitoring',
    '/responsible': 'responsible',
    '/admin': 'admin'
  };

  static viewToRoute = {
    'dashboard': '/dashboard',
    'dashboard-view': '/dashboard',
    'transactions': '/transactions',
    'transactions-view': '/transactions',
    'cases': '/cases',
    'cases-view': '/cases',
    'simulator': '/simulator',
    'simulator-view': '/simulator',
    'behavior': '/behavior',
    'behavior-view': '/behavior',
    'scam': '/scam',
    'scam-view': '/scam',
    'network': '/network',
    'network-view': '/network',
    'model': '/model',
    'model-view': '/model',
    'monitoring': '/monitoring',
    'monitoring-view': '/monitoring',
    'responsible': '/responsible',
    'responsible-view': '/responsible',
    'admin': '/admin',
    'admin-view': '/admin'
  };

  static async init() {
    // Intercept clicks on links or elements with data-route or data-view
    document.addEventListener('click', (e) => {
      const target = e.target.closest('[data-route], [data-view]');
      if (!target) return;

      const route = target.getAttribute('data-route');
      const viewId = target.getAttribute('data-view');

      if (route) {
        e.preventDefault();
        this.navigate(route);
      } else if (viewId) {
        e.preventDefault();
        const mappedRoute = this.viewToRoute[viewId] || '/dashboard';
        this.navigate(mappedRoute);
      }
    });

    // Handle browser Back / Forward buttons
    window.addEventListener('popstate', (e) => {
      this.resolveCurrentUrl(false);
    });

    // Initial resolution on page load
    await this.resolveCurrentUrl(false);
  }

  static async navigate(path, pushState = true) {
    const cleanPath = this.normalizePath(path);
    const viewName = this.routes[cleanPath] || 'dashboard';

    if (pushState && window.location.pathname !== cleanPath) {
      window.history.pushState({ path: cleanPath, viewName }, '', cleanPath);
    }

    await this.activateView(viewName, cleanPath);
  }

  static async resolveCurrentUrl(pushState = false) {
    const currentPath = this.normalizePath(window.location.pathname);
    const viewName = this.routes[currentPath] || 'dashboard';
    await this.activateView(viewName, currentPath);
  }

  static normalizePath(path) {
    if (!path || path === '' || path === '/') return '/dashboard';
    const trimmed = path.replace(/\/+$/, '');
    return trimmed.toLowerCase();
  }

  static async activateView(viewName, routePath) {
    const viewId = `${viewName}-view`;

    // 1. Mount dynamic view HTML template into workspace
    if (window.ComponentLoader) {
      try {
        await ComponentLoader.loadView(viewName);
      } catch (err) {
        console.error(`[AppRouter] Failed mounting view ${viewName}:`, err);
      }
    }

    // 2. Update navigation sidebar active button
    document.querySelectorAll('.nav-item').forEach(btn => {
      const btnView = btn.getAttribute('data-view');
      const btnRoute = btn.getAttribute('data-route');
      if (btnView === viewId || btnView === viewName || (btnRoute && btnRoute === routePath)) {
        btn.classList.add('active');
      } else {
        btn.classList.remove('active');
      }
    });

    // 3. Update topbar header titles
    if (window.ViewTitles && (window.ViewTitles[viewId] || window.ViewTitles[viewName])) {
      const info = window.ViewTitles[viewId] || window.ViewTitles[viewName];
      const titleElem = document.getElementById('current-view-title');
      const subtitleElem = document.getElementById('current-view-subtitle');
      if (titleElem) titleElem.innerText = info.title;
      if (subtitleElem) subtitleElem.innerText = info.subtitle;
      document.title = `${info.title} — upay AI Shield`;
    }

    if (window.AppState) {
      window.AppState.currentView = viewId;
    }

    // 4. Trigger view-specific data fetching on navigation
    if (viewName === 'cases' && typeof window.loadCasesLedger === 'function') {
      window.loadCasesLedger();
    } else if (viewName === 'transactions' && typeof window.loadTransactionsLedger === 'function') {
      window.loadTransactionsLedger();
    } else if (viewName === 'network' && typeof window.loadNetworkGraphForTx === 'function') {
      window.loadNetworkGraphForTx();
    } else if (viewName === 'admin' && typeof window.loadAdminViewData === 'function') {
      window.loadAdminViewData();
    } else if (viewName === 'behavior' && typeof window.lookupCustomerBehavior === 'function') {
      window.lookupCustomerBehavior();
    } else if (viewName === 'dashboard' && typeof window.refreshDashboardData === 'function') {
      window.refreshDashboardData();
    } else if (viewName === 'scam' && typeof window.loadScamTypologiesGrid === 'function') {
      window.loadScamTypologiesGrid();
    } else if (viewName === 'monitoring' && typeof window.loadModelDriftTable === 'function') {
      window.loadModelDriftTable();
    } else if (viewName === 'model' && typeof window.loadFeatureImportanceBars === 'function') {
      window.loadFeatureImportanceBars();
    }
  }
}

window.AppRouter = AppRouter;
