class AuthService {
  async login(email, password) {
    const res = await window.apiService.post('/auth/login', { email, password });
    if (res.data && res.data.access_token) {
      window.apiService.setToken(res.data.access_token);
    }
    return res;
  }

  async register(data) {
    const res = await window.apiService.post('/auth/register', data);
    if (res.data && res.data.access_token) {
      window.apiService.setToken(res.data.access_token);
    }
    return res;
  }

  me() {
    return window.apiService.get('/auth/me');
  }

  logout() {
    window.apiService.setToken(null);
    window.location.href = '/';
  }
}

window.authService = new AuthService();
