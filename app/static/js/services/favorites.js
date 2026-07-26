class FavoritesService {
  list() {
    return window.apiService.get('/favorites');
  }

  add(eventId) {
    return window.apiService.post(`/favorites/${eventId}`);
  }

  remove(eventId) {
    return window.apiService.delete(`/favorites/${eventId}`);
  }
}

window.favoritesService = new FavoritesService();
