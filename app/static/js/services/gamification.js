class GamificationService {
  getMe() {
    return window.apiService.get('/gamification/me');
  }

  getHistory(page = 1, perPage = 20) {
    return window.apiService.get(`/gamification/me/history?page=${page}&per_page=${perPage}`);
  }

  getLeaderboard() {
    return window.apiService.get('/gamification/leaderboard');
  }
}

window.gamificationService = new GamificationService();
