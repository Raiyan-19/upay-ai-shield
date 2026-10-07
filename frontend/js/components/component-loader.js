/**
 * Dynamic Component & Template Loader
 * Assembles modular HTML layout components, views, and modals on demand with in-memory caching.
 */
class ComponentLoader {
  static templateCache = {};

  static async fetchTemplate(url) {
    if (this.templateCache[url]) {
      return this.templateCache[url];
    }
    try {
      const res = await fetch(url);
      if (!res.ok) throw new Error(`HTTP ${res.status} fetching ${url}`);
      const html = await res.text();
      this.templateCache[url] = html;
      return html;
    } catch (err) {
      console.error(`[ComponentLoader] Error loading ${url}:`, err);
      throw err;
    }
  }

  static async mount(selector, templateUrl) {
    const container = document.querySelector(selector);
    if (!container) return;
    const html = await this.fetchTemplate(templateUrl);
    container.innerHTML = html;
  }

  static async mountAppend(selector, templateUrl) {
    const container = document.querySelector(selector);
    if (!container) return;
    const html = await this.fetchTemplate(templateUrl);
    const div = document.createElement('div');
    div.innerHTML = html;
    while (div.firstChild) {
      container.appendChild(div.firstChild);
    }
  }

  static async initLayout() {
    // Parallel mount of static layout shells & modals
    await Promise.all([
      this.mount('#sidebar-mount', '/components/layout/sidebar.html'),
      this.mount('#header-mount', '/components/layout/header.html'),
      this.mount('#drawer-mount', '/components/modals/investigation-drawer.html'),
      this.mount('#modal-mount', '/components/modals/auth-modal.html')
    ]);

    // Append modals
    await this.mountAppend('#modal-mount', '/components/modals/create-user-modal.html');
    await this.mountAppend('#modal-mount', '/components/modals/customer-appeal-modal.html');
  }

  static async loadView(viewName) {
    const container = document.getElementById('view-container');
    if (!container) return;

    const templateUrl = `/views/${viewName}.html`;
    const html = await this.fetchTemplate(templateUrl);
    container.innerHTML = html;

    // Ensure the mounted section has the active class
    const mountedSec = container.firstElementChild;
    if (mountedSec) {
      mountedSec.classList.add('active');
    }
  }
}

window.ComponentLoader = ComponentLoader;
