class OrganizationsService {
  list(params = {}) {
    return window.apiService.get('/organizations', params);
  }

  getById(id) {
    return window.apiService.get(`/organizations/${id}`);
  }

  create(data) {
    return window.apiService.post('/organizations', data);
  }

  update(id, data) {
    return window.apiService.put(`/organizations/${id}`, data);
  }

  getMe() {
    return window.apiService.get('/organizations/me');
  }

  async findMyOrg(userId) {
    try {
      const meRes = await this.getMe();
      const org = meRes.organization || (meRes.data && meRes.data.organization);
      if (org) return org;
    } catch (e) {
    }
    const res = await this.list({ per_page: 100 });
    const orgs = res && res.organizations ? res.organizations : [];
    return orgs.find(o => o.user_id === userId) || null;
  }
}

window.organizationsService = new OrganizationsService();
