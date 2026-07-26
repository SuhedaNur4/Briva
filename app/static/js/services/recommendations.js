class RecommendationsService {
  getForMe(params = {}) {
    return window.apiService.get('/recommendations/me', params);
  }

  explain(eventId, userContext = {}) {
    return window.apiService.post('/recommendations/explain', {
      event_id: Number(eventId),
      ...userContext
    });
  }

  recommend(userContext = {}) {
    return window.apiService.post('/recommendations', userContext);
  }
}

window.recommendationsService = new RecommendationsService();
