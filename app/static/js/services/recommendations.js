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

  evaluateApplicant(payload) {
    return window.apiService.post('/recommendations/evaluate-applicant', payload);
  }
}

window.recommendationsService = new RecommendationsService();
