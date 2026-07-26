document.addEventListener('DOMContentLoaded', async () => {
  const loginSection = document.getElementById('login-prompt-section');
  const dashContent = document.getElementById('dashboard-content');
  const userDisplayName = document.getElementById('user-display-name');
  const logoutBtn = document.getElementById('logout-btn');

  const loginEmail = document.getElementById('login-email');
  const loginPass = document.getElementById('login-pass');
  const doLoginBtn = document.getElementById('do-login-btn');

  const statTotal = document.getElementById('stat-total-apps');
  const statApproved = document.getElementById('stat-approved-apps');
  const statPending = document.getElementById('stat-pending-apps');

  const recsSkeleton = document.getElementById('recs-skeleton');
  const recsGrid = document.getElementById('recs-grid');
  const recsEmpty = document.getElementById('recs-empty');

  const upcomingGrid = document.getElementById('upcoming-grid');
  const upcomingEmpty = document.getElementById('upcoming-empty');

  const appsSkeleton = document.getElementById('apps-skeleton');
  const appsGrid = document.getElementById('apps-grid');
  const appsEmpty = document.getElementById('apps-empty');

  const favsGrid = document.getElementById('favs-grid');
  const favsEmpty = document.getElementById('favs-empty');

  const historyGrid = document.getElementById('history-grid');
  const historyEmpty = document.getElementById('history-empty');

  function showToast(message, type = 'success') {
    const container = document.getElementById('toast-container');
    if (!container) return;
    const item = document.createElement('div');
    item.className = `toast-item toast-${type}`;
    item.textContent = message;
    container.appendChild(item);
    setTimeout(() => {
      item.remove();
    }, 4000);
  }

  if (!window.apiService.getToken()) {
    if (loginSection) loginSection.style.display = 'block';
    if (dashContent) dashContent.style.display = 'none';
  } else {
    if (loginSection) loginSection.style.display = 'none';
    if (dashContent) dashContent.style.display = 'block';
    loadDashboard();
  }

  if (doLoginBtn) {
    doLoginBtn.addEventListener('click', async () => {
      const email = (loginEmail.value || '').trim();
      const pass = loginPass.value || '';
      if (!email || !pass) {
        showToast('E-posta ve şifre zorunludur.', 'error');
        return;
      }
      doLoginBtn.disabled = true;
      doLoginBtn.textContent = 'Giriş Yapılıyor...';
      try {
        await window.authService.login(email, pass);
        showToast('Giriş başarılı.');
        window.location.reload();
      } catch (error) {
        showToast(error.message || 'Giriş başarısız.', 'error');
        doLoginBtn.disabled = false;
        doLoginBtn.textContent = 'Giriş Yap';
      }
    });
  }

  if (logoutBtn) {
    logoutBtn.addEventListener('click', () => {
      window.authService.logout();
    });
  }

  async function loadDashboard() {
    loadUser();
    loadApplications();
    loadRecommendations();
    loadFavorites();
  }

  async function loadUser() {
    try {
      const res = await window.authService.me();
      const user = res.data.user || res.data;
      if (user) {
        const name = getattrOr(user, 'volunteer_profile.full_name', user.email || 'Gönüllü');
        if (userDisplayName) userDisplayName.textContent = name;
      }
    } catch (e) {
      if (userDisplayName) userDisplayName.textContent = 'Gönüllü';
    }
  }

  function getattrOr(obj, path, fallback) {
    try {
      return path.split('.').reduce((o, i) => o[i], obj) || fallback;
    } catch (e) {
      return fallback;
    }
  }

  async function loadApplications() {
    if (appsSkeleton) appsSkeleton.style.display = 'grid';
    try {
      const res = await window.applicationsService.getMy();
      const apps = res.data.applications || [];
      
      const total = apps.length;
      const approved = apps.filter(a => a.status === 'approved').length;
      const pending = apps.filter(a => a.status === 'pending').length;

      if (statTotal) statTotal.textContent = window.formatNumber(total);
      if (statApproved) statApproved.textContent = window.formatNumber(approved);
      if (statPending) statPending.textContent = window.formatNumber(pending);

      if (appsSkeleton) appsSkeleton.style.display = 'none';

      if (!apps.length) {
        if (appsEmpty) appsEmpty.style.display = 'block';
        if (upcomingEmpty) upcomingEmpty.style.display = 'block';
        if (historyEmpty) historyEmpty.style.display = 'block';
        return;
      }

      if (appsGrid) {
        appsGrid.style.display = 'flex';
        appsGrid.innerHTML = '';
        apps.forEach(app => {
          const ev = app.event || {};
          const statusText = app.status === 'approved' ? 'Onaylandı' : (app.status === 'pending' ? 'Değerlendirmede' : 'Reddedildi');
          const badgeClass = app.status === 'approved' ? 'status-approved' : (app.status === 'pending' ? 'status-pending' : 'status-rejected');
          const dateStr = window.formatDate(app.applied_at);

          const card = document.createElement('div');
          card.style.background = 'var(--surface-card)';
          card.style.border = '1px solid var(--border-subtle)';
          card.style.borderRadius = 'var(--radius-md)';
          card.style.padding = 'var(--space-4) var(--space-6)';
          card.style.display = 'flex';
          card.style.justifyContent = 'space-between';
          card.style.alignItems = 'center';
          card.style.flexWrap = 'wrap';
          card.style.gap = 'var(--space-3)';
          card.innerHTML = `
            <div>
              <h3 style="font-size: var(--text-base); margin-bottom: var(--space-1);">
                <a href="/events/${app.event_id}" style="color: var(--text-main); text-decoration: none;">${ev.title || `Etkinlik #${app.event_id}`}</a>
              </h3>
              <span style="font-size: var(--text-xs); color: var(--text-muted);">Başvuru Tarihi: ${dateStr}</span>
            </div>
            <div style="display: flex; align-items: center; gap: var(--space-3);">
              <span class="status-badge ${badgeClass}">${statusText}</span>
              ${app.status === 'pending' ? `<button type="button" class="btn btn-outline" style="font-size: var(--text-xs); padding: 4px 10px;" data-cancel-id="${app.id}">İptal Et</button>` : ''}
            </div>
          `;

          const cancelBtn = card.querySelector(`[data-cancel-id="${app.id}"]`);
          if (cancelBtn) {
            cancelBtn.addEventListener('click', async () => {
              if (confirm('Başvurunuzu iptal etmek istediğinize emin misiniz?')) {
                try {
                  await window.applicationsService.update(app.id, { status: 'cancelled' });
                  showToast('Başvuru iptal edildi.');
                  loadApplications();
                } catch (err) {
                  showToast(err.message || 'İptal işlemi başarısız.', 'error');
                }
              }
            });
          }

          appsGrid.appendChild(card);
        });
      }

      const now = new Date();
      const upcomingApps = apps.filter(a => {
        if (a.status !== 'approved') return false;
        if (!a.event || !a.event.start_date) return true;
        return new Date(a.event.start_date) >= now;
      });

      if (upcomingGrid) {
        upcomingGrid.innerHTML = '';
        if (!upcomingApps.length) {
          if (upcomingEmpty) upcomingEmpty.style.display = 'block';
        } else {
          if (upcomingEmpty) upcomingEmpty.style.display = 'none';
          upcomingApps.forEach(app => renderMiniCard(app.event, upcomingGrid, app.event_id));
        }
      }

      const pastApps = apps.filter(a => {
        if (!a.event || !a.event.start_date) return false;
        return new Date(a.event.start_date) < now;
      });

      if (historyGrid) {
        historyGrid.innerHTML = '';
        if (!pastApps.length) {
          if (historyEmpty) historyEmpty.style.display = 'block';
        } else {
          if (historyEmpty) historyEmpty.style.display = 'none';
          pastApps.forEach(app => {
            const ev = app.event || {};
            const item = document.createElement('div');
            item.style.background = 'var(--bg-subtle)';
            item.style.border = '1px solid var(--border-subtle)';
            item.style.borderRadius = 'var(--radius-md)';
            item.style.padding = 'var(--space-4) var(--space-6)';
            item.style.display = 'flex';
            item.style.justifyContent = 'space-between';
            item.style.alignItems = 'center';
            item.innerHTML = `
              <div>
                <strong style="font-size: var(--text-sm); display: block;">${ev.title || `Etkinlik #${app.event_id}`}</strong>
                <span style="font-size: var(--text-xs); color: var(--text-muted);">Tamamlanma Tarihi: ${window.formatDate(ev.start_date)}</span>
              </div>
              <span class="status-badge status-approved">Katılım Tamamlandı</span>
            `;
            historyGrid.appendChild(item);
          });
        }
      }

    } catch (e) {
      if (appsSkeleton) appsSkeleton.style.display = 'none';
      if (appsEmpty) {
        appsEmpty.style.display = 'block';
        appsEmpty.innerHTML = '<p style="color: var(--accent-orange);">Başvuru verileri yüklenirken bir hata oluştu.</p>';
      }
    }
  }

  async function loadRecommendations() {
    if (recsSkeleton) recsSkeleton.style.display = 'grid';
    try {
      const res = await window.recommendationsService.getForMe();
      const recs = res.data.recommendations || [];
      if (recsSkeleton) recsSkeleton.style.display = 'none';

      if (!recs.length) {
        if (recsEmpty) recsEmpty.style.display = 'block';
        return;
      }

      if (recsEmpty) recsEmpty.style.display = 'none';
      if (recsGrid) {
        recsGrid.style.display = 'grid';
        recsGrid.innerHTML = '';
        recs.slice(0, 3).forEach(rec => {
          const ev = rec.event || { id: rec.event_id, title: rec.event_title };
          const card = document.createElement('article');
          card.className = 'event-card';
          const badgeText = window.formatRecommendationBadge(rec, ev.city) || 'Önerilen Fırsat';
          card.innerHTML = `
            <div class="event-card-header" style="display: flex; justify-content: space-between; align-items: center; margin-bottom: var(--space-2);">
              <span style="background: var(--bg-surface-alt); color: var(--color-primary); padding: 4px 10px; border-radius: var(--radius-full); font-size: var(--text-xs); font-weight: 600; border: 1px solid var(--border-subtle);">Bu etkinlik sana uygun olabilir: ${badgeText}</span>
            </div>
            <div class="event-card-body">
              <h3 style="font-size: var(--text-base); margin-bottom: var(--space-2);">
                <a href="/events/${ev.id}" style="color: var(--text-main); text-decoration: none;">${ev.title || `Etkinlik #${ev.id}`}</a>
              </h3>
              <p style="font-size: var(--text-xs); color: var(--text-muted); margin-bottom: var(--space-4);">İlgi alanlarınız ve beceri kriterlerinizle yüksek uyum gösteriyor.</p>
            </div>
            <div class="event-card-footer" style="border-top: 1px solid var(--border-subtle); padding-top: var(--space-3);">
              <a href="/events/${ev.id}" class="btn btn-primary btn-block" style="width: 100%; text-align: center;">Uygunluk Nedenlerini Gör</a>
            </div>
          `;
          recsGrid.appendChild(card);
        });
      }
    } catch (e) {
      if (recsSkeleton) recsSkeleton.style.display = 'none';
      if (recsEmpty) recsEmpty.style.display = 'block';
    }
  }

  async function loadFavorites() {
    try {
      const res = await window.favoritesService.list();
      const favs = res.data.favorites || [];
      if (!favs.length) {
        if (favsEmpty) favsEmpty.style.display = 'block';
        if (favsGrid) favsGrid.innerHTML = '';
        return;
      }
      if (favsEmpty) favsEmpty.style.display = 'none';
      if (favsGrid) {
        favsGrid.innerHTML = '';
        favs.forEach(fav => {
          const card = document.createElement('article');
          card.className = 'event-card';
          card.innerHTML = `
            <div class="event-card-body">
              <h3 style="font-size: var(--text-base); margin-bottom: var(--space-2);">
                <a href="/events/${fav.event_id}" style="color: var(--text-main); text-decoration: none;">Etkinlik #${fav.event_id}</a>
              </h3>
              <span style="font-size: var(--text-xs); color: var(--text-muted); display: block; margin-bottom: var(--space-4);">Kaydedilme Tarihi: ${window.formatDate(fav.created_at)}</span>
            </div>
            <div class="event-card-footer" style="display: flex; gap: var(--space-2); border-top: 1px solid var(--border-subtle); padding-top: var(--space-3);">
              <a href="/events/${fav.event_id}" class="btn btn-primary" style="flex: 1; text-align: center;">İncele</a>
              <button type="button" class="btn btn-outline" data-remove-fav="${fav.event_id}">Kaldır</button>
            </div>
          `;
          const removeBtn = card.querySelector(`[data-remove-fav="${fav.event_id}"]`);
          removeBtn.addEventListener('click', async () => {
            try {
              await window.favoritesService.remove(fav.event_id);
              showToast('Etkinlik favorilerden çıkarıldı.');
              loadFavorites();
            } catch (err) {
              showToast(err.message || 'Hata oluştu.', 'error');
            }
          });
          favsGrid.appendChild(card);
        });
      }
    } catch (e) {
      if (favsEmpty) favsEmpty.style.display = 'block';
    }
  }

  function renderMiniCard(ev, container, fallbackId) {
    if (!ev) ev = { id: fallbackId, title: `Etkinlik #${fallbackId}` };
    const card = document.createElement('article');
    card.className = 'event-card';
    card.innerHTML = `
      <div class="event-card-body">
        <h3 style="font-size: var(--text-base); margin-bottom: var(--space-1);">
          <a href="/events/${ev.id}" style="color: var(--text-main); text-decoration: none;">${ev.title}</a>
        </h3>
        <span style="font-size: var(--text-xs); color: var(--text-muted); display: block;">Tarih: ${window.formatDate(ev.start_date)}</span>
      </div>
      <div class="event-card-footer" style="border-top: 1px solid var(--border-subtle); padding-top: var(--space-3);">
        <a href="/events/${ev.id}" class="btn btn-secondary btn-block" style="width: 100%; text-align: center;">Sayfasına Git</a>
      </div>
    `;
    container.appendChild(card);
  }
});
