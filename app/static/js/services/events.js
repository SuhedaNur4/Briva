class EventsService {
  list(params = {}) {
    return window.apiService.get('/events', params);
  }

  getById(id) {
    return window.apiService.get(`/events/${id}`);
  }

  create(data) {
    return window.apiService.post('/events', data);
  }

  update(id, data) {
    return window.apiService.put(`/events/${id}`, data);
  }

  apply(id, coverLetter = '') {
    return window.apiService.post(`/events/${id}/apply`, { cover_letter: coverLetter });
  }

  getApplications(id, params = {}) {
    return window.apiService.get(`/events/${id}/applications`, params);
  }
}

window.eventsService = new EventsService();
