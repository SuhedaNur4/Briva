class ApiService {
  constructor(baseUrl = '/api') {
    this.baseUrl = baseUrl;
  }

  getToken() {
    return localStorage.getItem('briva_token');
  }

  setToken(token) {
    if (token) {
      localStorage.setItem('briva_token', token);
    } else {
      localStorage.removeItem('briva_token');
    }
  }

  getHeaders(customHeaders = {}) {
    const headers = {
      'Content-Type': 'application/json',
      ...customHeaders
    };
    const token = this.getToken();
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }
    return headers;
  }

  async request(endpoint, options = {}) {
    const url = `${this.baseUrl}${endpoint}`;
    const config = {
      ...options,
      headers: this.getHeaders(options.headers || {})
    };
    try {
      const response = await fetch(url, config);
      const data = await response.json().catch(() => ({}));
      if (!response.ok) {
        let errorMsg = data.error || 'İstek başarısız oldu';
        if (response.status === 429) {
          const retryAfter = response.headers.get('Retry-After');
          errorMsg = retryAfter ? `Çok fazla deneme yaptınız. Lütfen ${retryAfter} saniye bekleyin.` : 'Çok fazla istek gönderdiniz, lütfen bekleyin.';
        } else if (response.headers.has('X-RateLimit-Remaining')) {
           const remaining = response.headers.get('X-RateLimit-Remaining');
           if (parseInt(remaining) <= 4) {
             errorMsg += ` (1 dakika içinde ${remaining} hakkınız kaldı)`;
           }
        }
        
        const errorObj = new Error(errorMsg);
        errorObj.status = response.status;
        errorObj.data = data;
        errorObj.remaining = response.headers.get('X-RateLimit-Remaining');
        throw errorObj;
      }
      return { data, status: response.status };
    } catch (error) {
      throw error;
    }
  }

  get(endpoint, params = {}) {
    const queryString = new URLSearchParams(params).toString();
    const fullPath = queryString ? `${endpoint}?${queryString}` : endpoint;
    return this.request(fullPath, { method: 'GET' });
  }

  post(endpoint, body = {}) {
    return this.request(endpoint, {
      method: 'POST',
      body: JSON.stringify(body)
    });
  }

  put(endpoint, body = {}) {
    return this.request(endpoint, {
      method: 'PUT',
      body: JSON.stringify(body)
    });
  }

  delete(endpoint) {
    return this.request(endpoint, { method: 'DELETE' });
  }
}

const apiService = new ApiService();
window.apiService = apiService;
