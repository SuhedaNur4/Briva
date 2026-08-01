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
      const meRes = await this.getMe().catch(() => null);
      if (meRes) {
        const org = (meRes.data && meRes.data.organization) || meRes.organization;
        if (org) return org;
      }
    } catch (e) {
      console.error(e);
    }
    const res = await this.list({ per_page: 100 }).catch(() => null);
    const orgs = res && res.data && res.data.organizations ? res.data.organizations : (res && res.organizations ? res.organizations : []);
    return orgs.find(o => o.user_id === userId) || null;
  }
}

window.organizationsService = new OrganizationsService();
