class VolunteersService {
  getMe() {
    return window.apiService.get('/volunteers/me');
  }

  updateMe(data) {
    return window.apiService.put('/volunteers/me', data);
  }

  getById(id) {
    return window.apiService.get(`/volunteers/${id}`);
  }

  list(params = {}) {
    return window.apiService.get('/volunteers', params);
  }
}

window.volunteersService = new VolunteersService();
