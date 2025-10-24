// Global helper functions for app-wide use
// Page-specific initialization is now handled in each template

// Toast notification helper
function showToast(message, type = 'info') {
  const toast = document.createElement('div');
  toast.className = `alert alert-${type} alert-dismissible fade show position-fixed top-0 end-0 m-3`;
  toast.style.zIndex = '9999';
  toast.innerHTML = `
    <i class="bi bi-${type === 'success' ? 'check-circle' : type === 'danger' ? 'x-circle' : 'info-circle'}-fill"></i>
    ${message}
    <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
  `;
  document.body.appendChild(toast);
  setTimeout(() => toast.remove(), 3000);
}

// CSRF token helper for fetch requests
function getCSRFToken() {
  const meta = document.querySelector('meta[name="csrf-token"]');
  return meta ? meta.content : '';
}

// Enhanced fetch with CSRF token
async function fetchWithCSRF(url, options = {}) {
  const token = getCSRFToken();
  if (token && options.method && options.method !== 'GET') {
    options.headers = {
      ...options.headers,
      'X-CSRFToken': token
    };
  }
  return fetch(url, options);
}
