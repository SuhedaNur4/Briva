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
  const statXpPoints = document.getElementById('stat-xp-points');

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


  // --- Auth Check ---
  if (!window.apiService.getToken()) {
    window.location.href = '/login';
    return;
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
        window.ui.showToast('E-posta ve şifre zorunludur.', 'error');
        return;
      }
      doLoginBtn.disabled = true;
      doLoginBtn.textContent = 'Giriş Yapılıyor...';
      try {
        await window.authService.login(email, pass);
        window.ui.showToast('Giriş başarılı.');
        window.location.reload();
      } catch (error) {
        window.ui.showToast(error.message || 'Giriş başarısız.', 'error');
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
    loadProfile();
    loadApplications();
    // loadRecommendations(); // Artık butona basılınca çağrılacak
    loadFavorites();
    loadGamification();
    loadXpHistory();
    loadLeaderboard();
    loadBiviProfile();
  }

  async function loadUser() {
    try {
      const res = await window.authService.me();
      const user = res.data.user || res.data;
      if (user) {
        const name = getattrOr(user, 'volunteer_profile.full_name', user.email || 'Gönüllü');
        if (userDisplayName) userDisplayName.textContent = name;
        
        const avatarInitial = document.getElementById('profile-avatar-initial');
        if (avatarInitial) {
          avatarInitial.textContent = name.charAt(0).toUpperCase();
        }
        
        if (statXpPoints) {
          statXpPoints.textContent = getattrOr(user, 'volunteer_profile.xp_points', 0);
        }
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

  const profileSkeleton = document.getElementById('profile-skeleton');
  const profileForm = document.getElementById('volunteer-profile-form');
  const profileSaveBtn = document.getElementById('profile-save-btn');
  const profileFormContainer = document.getElementById('profile-form-container');
  const btnToggleProfileForm = document.getElementById('btn-toggle-profile-form');
  const btnScrollToProfile = document.getElementById('btn-scroll-to-profile');

  // Phase 17B Elements
  const compLoading = document.getElementById('profile-completion-loading');
  const compContent = document.getElementById('profile-completion-content');
  const compError = document.getElementById('profile-completion-error');
  const compText = document.getElementById('profile-completion-text');
  const compPercent = document.getElementById('profile-completion-percentage-display');
  const compBar = document.getElementById('profile-completion-bar');
  const compSuccess = document.getElementById('profile-completion-success');
  const smartMatchHelper = document.getElementById('smart-match-profile-helper');

  if (btnToggleProfileForm) {
    btnToggleProfileForm.addEventListener('click', () => {
      profileFormContainer.style.display = 'block';
      profileForm.style.display = 'block';
      profileSkeleton.style.display = 'none';
    });
  }

  if (btnScrollToProfile) {
    btnScrollToProfile.addEventListener('click', (e) => {
      if (profileFormContainer) profileFormContainer.style.display = 'block';
      if (profileForm) profileForm.style.display = 'block';
      if (profileSkeleton) profileSkeleton.style.display = 'none';
    });
  }

  async function loadProfile() {
    if (!profileSkeleton || !profileForm) return;
    
    if (compLoading) compLoading.style.display = 'block';
    if (compContent) compContent.style.display = 'none';
    if (compError) compError.style.display = 'none';

    try {
      const res = await window.volunteersService.getMe();
      const vp = res.data.volunteer;
      if (vp) {
        document.getElementById('profile-first-name').value = vp.first_name || '';
        document.getElementById('profile-last-name').value = vp.last_name || '';
        document.getElementById('profile-phone').value = vp.phone || '';
        document.getElementById('profile-birth-date').value = vp.birth_date || '';
        document.getElementById('profile-city').value = vp.city || '';
        document.getElementById('profile-bio').value = vp.bio || '';
        document.getElementById('profile-skills').value = (vp.skills || []).join(', ');
        document.getElementById('profile-interests').value = (vp.interests || []).join(', ');
        
        try {
          const authRes = await window.authService.me();
          if (authRes.data && authRes.data.user) {
            document.getElementById('profile-email').value = authRes.data.user.email || '';
          }
        } catch (e) { console.error('Email yüklenemedi'); }

        // Phase 17B UX Updates
        const pct = vp.profile_completion_percentage || 0;
        
        if (compLoading) compLoading.style.display = 'none';
        if (compContent) compContent.style.display = 'block';
        
        if (compText) compText.textContent = `Profilin %${pct} tamamlandı`;
        if (compPercent) compPercent.textContent = `${pct}%`;
        if (compBar) {
          compBar.style.width = `${pct}%`;
          compBar.setAttribute('aria-valuenow', pct);
        }

        if (pct === 100) {
          if (compSuccess) compSuccess.style.display = 'block';
          if (btnToggleProfileForm) btnToggleProfileForm.style.display = 'none';
          if (smartMatchHelper) smartMatchHelper.style.display = 'none';
          if (profileFormContainer) profileFormContainer.style.display = 'none';
        } else {
          if (compSuccess) compSuccess.style.display = 'none';
          if (btnToggleProfileForm) btnToggleProfileForm.style.display = 'inline-block';
          if (smartMatchHelper) smartMatchHelper.style.display = 'block';
        }
      }
    } catch (e) {
      if (compLoading) compLoading.style.display = 'none';
      if (compError) compError.style.display = 'block';
    }
  }

  if (profileForm) {
    profileForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      if (profileSaveBtn.disabled) return;
      profileSaveBtn.disabled = true;
      profileSaveBtn.textContent = 'Kaydediliyor...';
      
      const payload = {
        first_name: document.getElementById('profile-first-name').value,
        last_name: document.getElementById('profile-last-name').value,
        phone: document.getElementById('profile-phone').value,
        birth_date: document.getElementById('profile-birth-date').value,
        city: document.getElementById('profile-city').value,
        bio: document.getElementById('profile-bio').value,
        skills: document.getElementById('profile-skills').value,
        interests: document.getElementById('profile-interests').value
      };

      try {
        await window.volunteersService.updateMe(payload);
        window.ui.showToast('Profil başarıyla güncellendi.');
        loadUser();
        // Live refresh Phase 17B
        await loadProfile();
        // Force gamification refresh since 100% gives XP/badges
        loadGamification();
        loadXpHistory();
      } catch (err) {
        window.ui.showToast(err.message || 'Profil güncellenirken bir hata oluştu.', 'error');
      } finally {
        profileSaveBtn.disabled = false;
        profileSaveBtn.textContent = 'Kaydet';
      }
    });
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
          let statusText = 'Durum bilgisi güncelleniyor';
          let badgeClass = 'status-pending';
          switch (app.status) {
            case 'pending': statusText = 'Değerlendiriliyor'; badgeClass = 'status-pending'; break;
            case 'approved': case 'accepted': statusText = 'Onaylandı'; badgeClass = 'status-approved'; break;
            case 'rejected': statusText = 'Reddedildi'; badgeClass = 'status-rejected'; break;
            case 'completed': statusText = 'Tamamlandı'; badgeClass = 'status-completed'; break;
            case 'cancelled': statusText = 'İptal Edildi'; badgeClass = 'status-cancelled'; break;
          }
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
                  window.ui.showToast('Başvuru iptal edildi.');
                  loadApplications();
                } catch (err) {
                  window.ui.showToast(err.message || 'İptal işlemi başarısız.', 'error');
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

  const btnSmartMatch = document.getElementById('btn-smart-match');
  if (btnSmartMatch) {
    btnSmartMatch.addEventListener('click', async () => {
      btnSmartMatch.disabled = true;
      btnSmartMatch.textContent = 'Aranıyor...';
      await loadRecommendations();
      btnSmartMatch.disabled = false;
      btnSmartMatch.textContent = 'Bana Etkinlik Bul';
    });
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
              <div style="font-size: var(--text-xs); color: var(--text-muted); margin-bottom: var(--space-4); display: flex; flex-direction: column; gap: 4px;">
              ${(rec.matching_details && Object.keys(rec.matching_details).length > 0 
                     ? Object.entries(rec.matching_details).filter(([k,v]) => (Array.isArray(v) ? v.length > 0 : v)).map(([k,v]) => `<span>✓ ${k === 'matching_skills' ? 'Becerilerinle örtüşüyor' : (k === 'matching_interests' ? 'İlgi alanlarınla örtüşüyor' : (k === 'city_matched' ? 'Konumuna uygun' : (k === 'day_matched' ? 'Müsaitlik gününle uyumlu' : 'Profilinle uyumlu')))}</span>`).join('') 
                     : '<span>✓ Profilinle genel olarak uyumlu</span>')}
              </div>
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
              window.ui.showToast('Etkinlik favorilerden çıkarıldı.');
              loadFavorites();
            } catch (err) {
              window.ui.showToast(err.message || 'Hata oluştu.', 'error');
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

  const gamRetryBtn = document.getElementById('gamification-retry-btn');
  if (gamRetryBtn) gamRetryBtn.addEventListener('click', loadGamification);

  async function loadGamification() {
    const gamSkeleton = document.getElementById('gamification-skeleton');
    const gamContent = document.getElementById('gamification-content');
    const gamEmpty = document.getElementById('gamification-empty');
    const gamEmptyText = document.getElementById('gamification-empty-text');

    if (gamSkeleton) gamSkeleton.style.display = 'block';
    if (gamContent) gamContent.style.display = 'none';
    if (gamEmpty) gamEmpty.style.display = 'none';
    
    try {
      const res = await window.gamificationService.getMe();
      const gam = res.data;
      if (gamSkeleton) gamSkeleton.style.display = 'none';
      
      if (!gam || gam.xp === undefined) {
        if (gamEmpty) {
          gamEmpty.style.display = 'block';
          if (gamEmptyText) gamEmptyText.textContent = 'Henüz İyilik Puanı kazanmadınız.';
        }
        return;
      }

      if (gamContent) gamContent.style.display = 'block';
      const levelEl = document.getElementById('gamification-level');
      if (levelEl) levelEl.textContent = gam.level;
      
      const xpEl = document.getElementById('gamification-xp');
      if (xpEl) xpEl.textContent = window.formatNumber(gam.xp) + ' İP';
      
      const nextXpEl = document.getElementById('gamification-next-xp');
      const nextXpTextEl = document.getElementById('gamification-next-xp-text');
      if (gam.next_level_xp === null) {
          if (nextXpTextEl) nextXpTextEl.textContent = 'Maksimum seviyedesiniz!';
      } else {
          if (nextXpEl) nextXpEl.textContent = window.formatNumber(gam.next_level_xp);
      }
      
      const pBar = document.getElementById('gamification-progress-bar');
      if (pBar) pBar.style.width = (gam.progress * 100) + '%';

      const badgesContainer = document.getElementById('gamification-badges');
      if (badgesContainer && gam.badges) {
        badgesContainer.innerHTML = '';
        gam.badges.forEach(ub => {
          const b = ub.badge;
          if (!b) return;
          const badgeEl = document.createElement('div');
          badgeEl.style.display = 'flex';
          badgeEl.style.alignItems = 'center';
          badgeEl.style.gap = 'var(--space-2)';
          badgeEl.style.background = 'var(--bg-surface-alt)';
          badgeEl.style.border = '1px solid var(--border-subtle)';
          badgeEl.style.borderRadius = 'var(--radius-full)';
          badgeEl.style.padding = '4px 12px';
          badgeEl.innerHTML = `
            <span style="font-size: var(--text-base);">🏆</span>
            <div>
              <strong style="font-size: var(--text-xs); display: block; color: var(--text-main);">${b.name}</strong>
            </div>
          `;
          badgeEl.title = b.description;
          badgesContainer.appendChild(badgeEl);
        });
      }

    } catch (e) {
      if (gamSkeleton) gamSkeleton.style.display = 'none';
      if (gamEmpty) {
        gamEmpty.style.display = 'block';
        if (gamEmptyText) gamEmptyText.textContent = 'Katkı bilgileriniz şu anda yüklenemiyor.';
      }
    }
  }

  async function loadXpHistory() {
    const skeleton = document.getElementById('xp-history-skeleton');
    const grid = document.getElementById('xp-history-grid');
    const empty = document.getElementById('xp-history-empty');

    if (skeleton) skeleton.style.display = 'block';
    
    try {
      const res = await window.gamificationService.getHistory(1, 10);
      const items = res.data.items || [];
      if (skeleton) skeleton.style.display = 'none';
      
      if (!items.length) {
        if (empty) empty.style.display = 'block';
        return;
      }
      
      if (grid) {
        grid.style.display = 'flex';
        grid.innerHTML = '';
        items.forEach(item => {
          const el = document.createElement('div');
          el.style.background = 'var(--bg-subtle)';
          el.style.border = '1px solid var(--border-subtle)';
          el.style.borderRadius = 'var(--radius-md)';
          el.style.padding = 'var(--space-3) var(--space-4)';
          el.style.display = 'flex';
          el.style.justifyContent = 'space-between';
          el.style.alignItems = 'center';
          el.innerHTML = `
            <div>
              <strong style="font-size: var(--text-sm); display: block;">${item.reason}</strong>
              <span style="font-size: var(--text-xs); color: var(--text-muted);">${window.formatDate(item.created_at)}</span>
            </div>
            <strong style="color: var(--primary-main); font-size: var(--text-base);">+${item.amount} İP</strong>
          `;
          grid.appendChild(el);
        });
      }
    } catch (e) {
      if (skeleton) skeleton.style.display = 'none';
      if (empty) {
        empty.style.display = 'block';
        empty.querySelector('p').textContent = 'Geçmiş bilgileri yüklenemedi.';
      }
    }
  }

  async function loadLeaderboard() {
    const skeleton = document.getElementById('leaderboard-skeleton');
    const grid = document.getElementById('leaderboard-grid');
    const errorEl = document.getElementById('leaderboard-error');

    if (skeleton) skeleton.style.display = 'block';
    
    try {
      const res = await window.gamificationService.getLeaderboard();
      const entries = res.data.entries || [];
      const current = res.data.current_user;
      if (skeleton) skeleton.style.display = 'none';
      
      if (!entries.length) {
        if (errorEl) errorEl.style.display = 'block';
        return;
      }
      
      if (grid) {
        grid.style.display = 'flex';
        grid.innerHTML = '';
        entries.forEach(entry => {
          const isMe = current && current.rank === entry.rank;
          const el = document.createElement('div');
          el.style.padding = 'var(--space-3) var(--space-4)';
          el.style.borderBottom = '1px solid var(--border-subtle)';
          el.style.display = 'flex';
          el.style.justifyContent = 'space-between';
          el.style.alignItems = 'center';
          if (isMe) {
            el.style.background = 'var(--bg-surface-alt)';
          }
          el.innerHTML = `
            <div style="display: flex; align-items: center; gap: var(--space-3);">
              <span style="font-size: var(--text-lg); font-weight: bold; color: var(--text-muted); min-width: 24px;">#${entry.rank}</span>
              <strong style="font-size: var(--text-sm); color: ${isMe ? 'var(--primary-main)' : 'var(--text-main)'};">${isMe ? 'Sen: ' : ''}${entry.display_name}</strong>
            </div>
            <strong style="font-size: var(--text-sm); color: var(--text-muted);">${window.formatNumber(entry.xp)} İP</strong>
          `;
          grid.appendChild(el);
        });
        if (grid.lastElementChild) grid.lastElementChild.style.borderBottom = 'none';
      }
    } catch (e) {
      if (skeleton) skeleton.style.display = 'none';
      if (errorEl) errorEl.style.display = 'block';
    }
  }

  async function loadBiviProfile() {
    const section = document.getElementById('bivi-profile-section');
    const interestsContainer = document.getElementById('bivi-interests-container');
    const skillsContainer = document.getElementById('bivi-skills-container');
    if (!section || !interestsContainer || !skillsContainer) return;

    try {
      const res = await window.volunteersService.getMe();
      const vp = res.data.volunteer;
      if (vp && (vp.interests.length > 0 || vp.skills.length > 0)) {
        section.style.display = 'block';
        
        interestsContainer.innerHTML = '';
        if (vp.interests && vp.interests.length > 0) {
          vp.interests.forEach(interest => {
            const el = document.createElement('span');
            el.style.background = '#e8f0eb';
            el.style.color = '#093424';
            el.style.padding = '6px 16px';
            el.style.borderRadius = '99px';
            el.style.fontSize = '0.9rem';
            el.style.fontWeight = '600';
            el.style.border = '1px solid #d4e4da';
            el.textContent = interest.charAt(0).toUpperCase() + interest.slice(1);
            interestsContainer.appendChild(el);
          });
        } else {
          interestsContainer.innerHTML = '<span style="color:var(--text-muted);font-size:0.9rem;">Belirtilmemiş</span>';
        }

        skillsContainer.innerHTML = '';
        if (vp.skills && vp.skills.length > 0) {
          vp.skills.forEach(skill => {
            const el = document.createElement('span');
            el.style.background = '#fff4e5';
            el.style.color = '#b37400';
            el.style.padding = '6px 16px';
            el.style.borderRadius = '99px';
            el.style.fontSize = '0.9rem';
            el.style.fontWeight = '600';
            el.style.border = '1px solid #ffe8cc';
            el.textContent = skill.charAt(0).toUpperCase() + skill.slice(1);
            skillsContainer.appendChild(el);
          });
        } else {
          skillsContainer.innerHTML = '<span style="color:var(--text-muted);font-size:0.9rem;">Belirtilmemiş</span>';
        }
      } else {
        section.style.display = 'none';
      }
    } catch (e) {
      console.warn('Bivi profil verisi yüklenemedi', e);
    }
  }

  // --- Profile Modal Logic ---
  const editProfileBtn = document.getElementById('edit-profile-btn');
  const profileModal = document.getElementById('profile-modal');
  const closeProfileModalBtn = document.getElementById('close-profile-modal');
  const profileForm2 = document.getElementById('profile-form');
  const profError = document.getElementById('prof-error');
  const profSubmitBtn = document.getElementById('prof-submit-btn');

  if (editProfileBtn && profileModal) {
    editProfileBtn.addEventListener('click', async () => {
      // Fetch current profile and populate
      try {
        const res = await window.volunteersService.getMe();
        const vp = res.data.volunteer;
        if (vp) {
          document.getElementById('prof-firstname').value = vp.first_name || '';
          document.getElementById('prof-lastname').value = vp.last_name || '';
          document.getElementById('prof-phone').value = vp.phone || '';
          document.getElementById('prof-city').value = vp.city || '';
          document.getElementById('prof-birthdate').value = vp.birth_date || '';
          document.getElementById('prof-interests').value = (vp.interests || []).join(', ');
          document.getElementById('prof-skills').value = (vp.skills || []).join(', ');
          document.getElementById('prof-bio').value = vp.bio || '';
        }
      } catch (e) {
        console.warn('Profil verisi alınamadı:', e);
      }
      profileModal.style.display = 'flex';
    });
  }

  if (closeProfileModalBtn && profileModal) {
    closeProfileModalBtn.addEventListener('click', () => {
      profileModal.style.display = 'none';
      if (profError) profError.style.display = 'none';
    });
  }

  if (profileForm2) {
    profileForm2.addEventListener('submit', async (e) => {
      e.preventDefault();
      if (profSubmitBtn.disabled) return;
      
      const payload = {
        first_name: document.getElementById('prof-firstname').value.trim(),
        last_name: document.getElementById('prof-lastname').value.trim(),
        phone: document.getElementById('prof-phone').value.trim(),
        city: document.getElementById('prof-city').value.trim(),
        birth_date: document.getElementById('prof-birthdate').value.trim(),
        bio: document.getElementById('prof-bio').value.trim(),
        interests: document.getElementById('prof-interests').value.split(',').map(s => s.trim()).filter(Boolean),
        skills: document.getElementById('prof-skills').value.split(',').map(s => s.trim()).filter(Boolean)
      };

      profSubmitBtn.disabled = true;
      profSubmitBtn.textContent = 'Kaydediliyor...';
      if (profError) profError.style.display = 'none';

      try {
        await window.apiService.put('/api/volunteers/me', payload);
        window.ui.showToast('Profil başarıyla güncellendi.', 'success');
        profileModal.style.display = 'none';
        window.location.reload();
      } catch (error) {
        if (profError) {
          profError.style.display = 'block';
          profError.textContent = error.message || 'Profil güncellenirken bir hata oluştu.';
        }
        window.ui.showToast('Profil kaydedilemedi.', 'error');
      } finally {
        profSubmitBtn.disabled = false;
        profSubmitBtn.textContent = 'Kaydet';
      }
    });
  }

});
