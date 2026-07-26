class ApplicationsService {
  getMy(params = {}) {
    return window.apiService.get('/applications/my', params);
  }

  update(id, data) {
    return window.apiService.put(`/applications/${id}`, data);
  }
}

window.applicationsService = new ApplicationsService();
