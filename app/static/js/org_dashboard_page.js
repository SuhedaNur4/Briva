document.addEventListener('DOMContentLoaded', async () => {
  const loginPrompt = document.getElementById('org-login-prompt');
  const createOrgPrompt = document.getElementById('org-create-profile-prompt');
  const dashContent = document.getElementById('org-dashboard-content');

  const doLoginBtn = document.getElementById('org-do-login-btn');
  if (doLoginBtn) {
    doLoginBtn.addEventListener('click', async () => {
      const email = document.getElementById('org-login-email').value.trim();
      const password = document.getElementById('org-login-pass').value.trim();
      if (!email || !password) {
        window.ui.showToast('E-posta ve şifre gereklidir.', 'error');
        return;
      }
      doLoginBtn.disabled = true;
      doLoginBtn.textContent = 'Oturum Açılıyor...';
      const res = await window.authService.login(email, password);
      doLoginBtn.disabled = false;
      doLoginBtn.textContent = 'STK Olarak Giriş Yap';
      if (res && res.error) {
        window.ui.showToast(res.error, 'error');
      } else {
        window.ui.showToast('Giriş başarılı!', 'success');
        window.location.reload();
      }
    });
  }

  const logoutBtn = document.getElementById('org-logout-btn');
  if (logoutBtn) {
    logoutBtn.addEventListener('click', () => {
      window.authService.logout();
      window.location.reload();
    });
  }

  let meRes = await window.authService.me().catch(() => null);
  let user = meRes && meRes.data && meRes.data.user ? meRes.data.user : null;

  if (!user || user.role !== 'organization') {
    window.location.href = '/login';
    return;
  }

  let org = await window.organizationsService.findMyOrg(user.id);
  if (!org) {
    if (createOrgPrompt) {
      createOrgPrompt.style.display = 'block';
      const createBtn = document.getElementById('create-org-btn');
      createBtn.addEventListener('click', async () => {
        const name = document.getElementById('new-org-name').value.trim();
        const city = document.getElementById('new-org-city').value.trim();
        const description = document.getElementById('new-org-desc').value.trim();
        if (!name) {
          window.ui.showToast('Kuruluş adı zorunludur.', 'error');
          return;
        }
        createBtn.disabled = true;
        createBtn.textContent = 'Kaydediliyor...';
        const res = await window.organizationsService.create({ name, city, description }).catch(err => ({ error: err.message }));
        createBtn.disabled = false;
        createBtn.textContent = 'Profili Kaydet ve Başla';
        if (res && res.error) {
          window.ui.showToast(res.error, 'error');
        } else {
          window.ui.showToast('STK profili başarıyla oluşturuldu.', 'success');
          window.location.reload();
        }
      });
    }
    return;
  }

  if (dashContent) dashContent.style.display = 'block';

  document.getElementById('org-header-name').textContent = org.name;
  
  const headerLogoEl = document.getElementById('org-header-logo');
  if (headerLogoEl) {
    const cleanDomain = org.website ? org.website.replace(/^https?:\/\//, '').replace(/^www\./, '').split('/')[0] : '';
    const defaultLogo = `https://ui-avatars.com/api/?name=${encodeURIComponent(org.name || 'STK')}&background=random`;
    headerLogoEl.src = org.logo_url || (cleanDomain ? `https://logo.clearbit.com/${cleanDomain}` : defaultLogo);
    headerLogoEl.onerror = function() { this.src = defaultLogo; this.onerror = null; };
  }

  if (org.is_verified) {
    const vTag = document.getElementById('org-verified-tag');
    if (vTag) vTag.style.display = 'inline-block';
  }

  let allEvents = [];
  let allApps = [];

  const loadDashboardData = async () => {
    const evRes = await window.eventsService.list({ organization_id: org.id, status: 'all' });
    allEvents = evRes && evRes.data && evRes.data.events ? evRes.data.events : (evRes && evRes.events ? evRes.events : []);
    allApps = [];

    for (const ev of allEvents) {
      const appRes = await window.eventsService.getApplications(ev.id);
      const apps = appRes && appRes.data && appRes.data.applications ? appRes.data.applications : (appRes && appRes.applications ? appRes.applications : null);
      if (apps) {
        apps.forEach(a => {
          allApps.push({ ...a, event_title: ev.title });
        });
      }
    }

    renderSummary();
    renderActiveEvents();
    renderPendingApps();
    renderUpcomingEvents();
    renderAllEvents();
    renderAllApps();
    fillProfileForm();
  };

  const renderSummary = () => {
    document.getElementById('stat-org-total-events').textContent = window.formatNumber(allEvents.length);
    const pubCount = allEvents.filter(e => e.status === 'published').length;
    document.getElementById('stat-org-published-events').textContent = window.formatNumber(pubCount);
    const pendCount = allApps.filter(a => a.status === 'pending').length;
    document.getElementById('stat-org-pending-apps').textContent = window.formatNumber(pendCount);
    const appCount = allApps.filter(a => a.status === 'approved').length;
    document.getElementById('stat-org-approved-apps').textContent = window.formatNumber(appCount);

    const now = new Date();
    const upcomingCount = allEvents.filter(e => e.status === 'published' && e.start_date && new Date(e.start_date) > now && (new Date(e.start_date) - now) <= 7 * 24 * 60 * 60 * 1000).length;
    const nearlyFullCount = allEvents.filter(e => e.status === 'published' && e.max_volunteers && e.max_volunteers > 0 && e.approved_count >= Math.floor(e.max_volunteers * 0.8) && !e.is_full).length;

    const banner = document.getElementById('org-action-required-banner');
    const list = document.getElementById('org-action-required-list');
    if (banner && list) {
      const items = [];
      if (pendCount > 0) items.push(`<strong>${pendCount} başvuru</strong> değerlendirmeyi bekliyor.`);
      if (upcomingCount > 0) items.push(`<strong>${upcomingCount} etkinliğin</strong> yaklaşıyor (önümüzdeki 7 gün içinde).`);
      if (nearlyFullCount > 0) items.push(`<strong>${nearlyFullCount} etkinliğin</strong> kontenjanı dolmak üzere (%80 ve üzeri doluluk).`);

      if (items.length > 0) {
        list.innerHTML = items.map(it => `<li style="margin-bottom: 4px;">${it}</li>`).join('');
        banner.style.display = 'block';
      } else {
        banner.style.display = 'none';
      }
    }
  };

  const renderActiveEvents = () => {
    const skel = document.getElementById('active-events-skeleton');
    const grid = document.getElementById('active-events-grid');
    const empty = document.getElementById('active-events-empty');
    if (skel) skel.style.display = 'none';

    const pub = allEvents.filter(e => e.status === 'published');
    if (pub.length === 0) {
      if (grid) grid.style.display = 'none';
      if (empty) empty.style.display = 'block';
      return;
    }
    if (empty) empty.style.display = 'none';
    if (grid) {
      grid.style.display = 'grid';
      grid.innerHTML = pub.map(ev => {
        const dateStr = window.formatDate(ev.start_date);
        const loc = ev.city || 'Konum belirtilmedi';
        const quota = ev.max_volunteers ? `${ev.approved_count} / ${ev.max_volunteers}` : `${ev.approved_count} Onaylı`;
        return `
          <div class="event-card">
            <div class="card-header" style="display: flex; flex-wrap: wrap; gap: 8px; justify-content: space-between;">
              <div style="display: flex; gap: 8px; flex-wrap: wrap;">
                <span class="event-category">${ev.category || 'Genel'}</span>
                <span style="background: rgba(245, 158, 11, 0.1); color: #d97706; padding: 4px 8px; border-radius: 8px; font-size: 0.75rem; font-weight: 700; border: 1px solid rgba(245, 158, 11, 0.2); white-space: nowrap;">+5 İyilik Puanı</span>
              </div>
              <span class="event-status published">Yayında</span>
            </div>
            <h3 class="event-title">${ev.title}</h3>
            <p class="event-meta">
              <span>${dateStr}</span>
              <span>•</span>
              <span>${loc}</span>
            </p>
            <div style="margin: var(--space-4) 0; font-size: var(--text-sm); color: var(--text-muted); display: flex; justify-content: space-between; background: var(--bg-subtle); padding: var(--space-2) var(--space-3); border-radius: var(--radius-sm);">
              <span>Kontenjan Doluluğu:</span>
              <strong style="color: var(--text-main);">${quota}</strong>
            </div>
            <div class="card-footer" style="justify-content: flex-end;">
              <a href="#applications" class="btn btn-outline btn-sm org-tab-link" data-tab="applications">Başvuruları İncele</a>
            </div>
          </div>
        `;
      }).join('');
      attachTabLinks();
    }
  };

  const updateAppStatus = async (appId, newStatus, btnEl) => {
    if (btnEl) {
      btnEl.disabled = true;
      btnEl.textContent = 'İşleniyor...';
    }
    const res = await window.applicationsService.update(appId, { status: newStatus });
    if (res && res.error) {
      window.ui.showToast(res.error, 'error');
      if (btnEl) {
        btnEl.disabled = false;
        btnEl.textContent = newStatus === 'approved' ? 'Onayla' : 'Reddet';
      }
    } else {
      window.ui.showToast(`Başvuru ${newStatus === 'approved' ? 'onaylandı' : 'reddedildi'}.`, 'success');
      await loadDashboardData();
    }
  };

  const renderPendingApps = () => {
    const skel = document.getElementById('pending-apps-skeleton');
    const container = document.getElementById('pending-apps-container');
    const empty = document.getElementById('pending-apps-empty');
    if (skel) skel.style.display = 'none';

    const pend = allApps.filter(a => a.status === 'pending');
    if (pend.length === 0) {
      if (container) container.style.display = 'none';
      if (empty) empty.style.display = 'block';
      return;
    }
    if (empty) empty.style.display = 'none';
    if (container) container.style.display = 'block';

    const tbody = document.getElementById('pending-apps-table-body');
    if (tbody) {
      tbody.innerHTML = pend.map(a => {
        const volName = (a.volunteer && a.volunteer.full_name) ? a.volunteer.full_name : ((a.volunteer && a.volunteer.email) ? a.volunteer.email : `Gönüllü #${a.user_id}`);
        const evTitle = a.event_title || (a.event ? a.event.title : `Etkinlik #${a.event_id}`);
        const dateStr = window.formatDate(a.applied_at);
        const note = a.cover_letter || '-';
        return `
          <tr>
            <td><strong>${volName}</strong></td>
            <td>${evTitle}</td>
            <td>${dateStr}</td>
            <td><div style="max-width: 200px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">${note}</div></td>
            <td>
              <div class="applicant-actions-group">
                <button type="button" class="btn btn-outline btn-sm act-view-btn" data-id="${a.id}">İncele</button>
                <button type="button" class="btn btn-primary btn-sm act-approve-btn" data-id="${a.id}">Onayla</button>
                <button type="button" class="btn btn-outline btn-sm act-reject-btn" data-id="${a.id}">Reddet</button>
              </div>
            </td>
          </tr>
        `;
      }).join('');
    }

    const mobileList = document.getElementById('pending-apps-mobile-list');
    if (mobileList) {
      mobileList.innerHTML = pend.map(a => {
        const volName = (a.volunteer && a.volunteer.full_name) ? a.volunteer.full_name : ((a.volunteer && a.volunteer.email) ? a.volunteer.email : `Gönüllü #${a.user_id}`);
        const evTitle = a.event_title || (a.event ? a.event.title : `Etkinlik #${a.event_id}`);
        const dateStr = window.formatDate(a.applied_at);
        const note = a.cover_letter || 'Not eklenmedi.';
        return `
          <div class="applicant-card-item">
            <div style="display: flex; justify-content: space-between; align-items: flex-start;">
              <strong style="font-size: var(--text-base); color: var(--text-main);">${volName}</strong>
              <span class="event-status pending">Değerlendirmede</span>
            </div>
            <div style="font-size: var(--text-sm); color: var(--text-muted);">
              <div><strong>Etkinlik:</strong> ${evTitle}</div>
              <div><strong>Tarih:</strong> ${dateStr}</div>
              <div style="margin-top: var(--space-2); background: var(--bg-subtle); padding: var(--space-2); border-radius: var(--radius-sm); font-style: italic;">"${note}"</div>
            </div>
            <div class="applicant-actions-group" style="margin-top: var(--space-2);">
              <button type="button" class="btn btn-outline btn-sm act-view-btn" data-id="${a.id}" style="flex: 1;">İncele</button>
              <button type="button" class="btn btn-primary btn-sm act-approve-btn" data-id="${a.id}" style="flex: 1;">Onayla</button>
              <button type="button" class="btn btn-outline btn-sm act-reject-btn" data-id="${a.id}" style="flex: 1;">Reddet</button>
            </div>
          </div>
        `;
      }).join('');
    }

    document.querySelectorAll('.act-approve-btn').forEach(btn => {
      btn.addEventListener('click', (e) => {
        const appId = e.currentTarget.getAttribute('data-id');
        updateAppStatus(appId, 'approved', e.currentTarget);
      });
    });
    document.querySelectorAll('.act-reject-btn').forEach(btn => {
      btn.addEventListener('click', (e) => {
        const appId = e.currentTarget.getAttribute('data-id');
        updateAppStatus(appId, 'rejected', e.currentTarget);
      });
    });
    document.querySelectorAll('.act-view-btn').forEach(btn => {
      btn.addEventListener('click', (e) => {
        const appId = e.currentTarget.getAttribute('data-id');
        openApplicantModal(appId);
      });
    });
  };

  const renderUpcomingEvents = () => {
    const grid = document.getElementById('upcoming-events-grid');
    const empty = document.getElementById('upcoming-events-empty');
    const now = new Date();
    const up = allEvents.filter(e => new Date(e.start_date) > now).sort((a, b) => new Date(a.start_date) - new Date(b.start_date));

    if (up.length === 0) {
      if (grid) grid.style.display = 'none';
      if (empty) empty.style.display = 'block';
      return;
    }
    if (empty) empty.style.display = 'none';
    if (grid) {
      grid.style.display = 'grid';
      grid.innerHTML = up.map(ev => {
        const dateStr = window.formatDate(ev.start_date);
        const loc = ev.city || 'Konum belirtilmedi';
        return `
          <div class="event-card">
            <div class="card-header">
              <span class="event-category">${ev.category || 'Genel'}</span>
              <span class="event-status approved">Yaklaşıyor</span>
            </div>
            <h3 class="event-title">${ev.title}</h3>
            <p class="event-meta">
              <span>${dateStr}</span>
              <span>•</span>
              <span>${loc}</span>
            </p>
            <div class="card-footer" style="justify-content: flex-end;">
              <a href="#events" class="btn btn-outline btn-sm org-tab-link" data-tab="events">Yönet</a>
            </div>
          </div>
        `;
      }).join('');
      attachTabLinks();
    }
  };

  const renderAllEvents = (statusFilter = 'all') => {
    const grid = document.getElementById('all-events-grid');
    const empty = document.getElementById('all-events-empty');
    let filtered = allEvents;
    if (statusFilter !== 'all') {
      filtered = allEvents.filter(e => e.status === statusFilter);
    }
    if (filtered.length === 0) {
      if (grid) grid.style.display = 'none';
      if (empty) empty.style.display = 'block';
      return;
    }
    if (empty) empty.style.display = 'none';
    if (grid) {
      grid.style.display = 'grid';
      grid.innerHTML = filtered.map(ev => {
        const dateStr = window.formatDate(ev.start_date);
        const loc = ev.city || 'Konum belirtilmedi';
        const stClass = ev.status === 'published' ? 'published' : (ev.status === 'completed' ? 'approved' : 'pending');
        const stLabel = ev.status === 'published' ? 'Yayında' : (ev.status === 'completed' ? 'Tamamlandı' : 'Taslak');
        return `
          <div class="event-card">
            <div class="card-header">
              <span class="event-category">${ev.category || 'Genel'}</span>
              <span class="event-status ${stClass}">${stLabel}</span>
            </div>
            <h3 class="event-title">${ev.title}</h3>
            <p class="event-meta">
              <span>${dateStr}</span>
              <span>•</span>
              <span>${loc}</span>
            </p>
            <p class="event-description" style="margin-bottom: var(--space-4);">${ev.description || 'Açıklama girilmemiş.'}</p>
            <div class="card-footer" style="justify-content: space-between; align-items: center;">
              <span style="font-size: var(--text-xs); color: var(--text-muted);">Kontenjan: ${ev.approved_count}/${ev.max_volunteers || '∞'}</span>
              <div style="display: flex; gap: 8px;">
                <button type="button" class="btn btn-outline btn-sm act-edit-ev-btn" data-id="${ev.id}">Düzenle</button>
                <a href="/events/${ev.id}" class="btn btn-outline btn-sm" target="_blank">Sayfayı Gör</a>
              </div>
            </div>
          </div>
        `;
      }).join('');
      
      document.querySelectorAll('.act-edit-ev-btn').forEach(btn => {
        btn.addEventListener('click', (e) => {
          const evId = e.currentTarget.getAttribute('data-id');
          openEditEventModal(evId);
        });
      });
    }
  };

  const renderAllApps = (statusFilter = 'all') => {
    const container = document.getElementById('all-apps-container');
    const empty = document.getElementById('all-apps-empty');
    let filtered = allApps;
    if (statusFilter !== 'all') {
      filtered = allApps.filter(a => a.status === statusFilter);
    }
    if (filtered.length === 0) {
      if (container) container.style.display = 'none';
      if (empty) empty.style.display = 'block';
      return;
    }
    if (empty) empty.style.display = 'none';
    if (container) container.style.display = 'block';

    const tbody = document.getElementById('all-apps-table-body');
    if (tbody) {
      tbody.innerHTML = filtered.map(a => {
        const volName = (a.volunteer && a.volunteer.full_name) ? a.volunteer.full_name : ((a.volunteer && a.volunteer.email) ? a.volunteer.email : `Gönüllü #${a.user_id}`);
        const evTitle = a.event_title || (a.event ? a.event.title : `Etkinlik #${a.event_id}`);
        const dateStr = window.formatDate(a.applied_at);
        const note = a.cover_letter || '-';
        const stClass = a.status === 'approved' ? 'approved' : (a.status === 'rejected' || a.status === 'cancelled' ? 'rejected' : 'pending');
        const stLabel = a.status === 'approved' ? 'Onaylandı' : (a.status === 'rejected' ? 'Reddedildi' : (a.status === 'cancelled' ? 'İptal' : 'Bekliyor'));
        let actionsHtml = `<button type="button" class="btn btn-outline btn-sm act-view-btn" data-id="${a.id}">İncele</button>`;
        if (a.status === 'pending') {
          actionsHtml = `
            <div class="applicant-actions-group">
              <button type="button" class="btn btn-outline btn-sm act-view-btn" data-id="${a.id}">İncele</button>
              <button type="button" class="btn btn-primary btn-sm act-all-app-btn" data-id="${a.id}" data-st="approved">Onayla</button>
              <button type="button" class="btn btn-outline btn-sm act-all-app-btn" data-id="${a.id}" data-st="rejected">Reddet</button>
            </div>
          `;
        }
        return `
          <tr>
            <td><strong>${volName}</strong></td>
            <td>${evTitle}</td>
            <td>${dateStr}</td>
            <td><div style="max-width: 180px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">${note}</div></td>
            <td><span class="event-status ${stClass}">${stLabel}</span></td>
            <td>${actionsHtml}</td>
          </tr>
        `;
      }).join('');
    }

    const mobileList = document.getElementById('all-apps-mobile-list');
    if (mobileList) {
      mobileList.innerHTML = filtered.map(a => {
        const volName = (a.volunteer && a.volunteer.full_name) ? a.volunteer.full_name : ((a.volunteer && a.volunteer.email) ? a.volunteer.email : `Gönüllü #${a.user_id}`);
        const evTitle = a.event_title || (a.event ? a.event.title : `Etkinlik #${a.event_id}`);
        const dateStr = window.formatDate(a.applied_at);
        const note = a.cover_letter || 'Not eklenmedi.';
        const stClass = a.status === 'approved' ? 'approved' : (a.status === 'rejected' || a.status === 'cancelled' ? 'rejected' : 'pending');
        const stLabel = a.status === 'approved' ? 'Onaylandı' : (a.status === 'rejected' ? 'Reddedildi' : (a.status === 'cancelled' ? 'İptal' : 'Bekliyor'));
        let actionsHtml = `<div class="applicant-actions-group" style="margin-top: var(--space-2);"><button type="button" class="btn btn-outline btn-sm act-view-btn" data-id="${a.id}" style="flex: 1;">İncele</button></div>`;
        if (a.status === 'pending') {
          actionsHtml = `
            <div class="applicant-actions-group" style="margin-top: var(--space-2);">
              <button type="button" class="btn btn-outline btn-sm act-view-btn" data-id="${a.id}" style="flex: 1;">İncele</button>
              <button type="button" class="btn btn-primary btn-sm act-all-app-btn" data-id="${a.id}" data-st="approved" style="flex: 1;">Onayla</button>
              <button type="button" class="btn btn-outline btn-sm act-all-app-btn" data-id="${a.id}" data-st="rejected" style="flex: 1;">Reddet</button>
            </div>
          `;
        }
        return `
          <div class="applicant-card-item">
            <div style="display: flex; justify-content: space-between; align-items: flex-start;">
              <strong style="font-size: var(--text-base); color: var(--text-main);">${volName}</strong>
              <span class="event-status ${stClass}">${stLabel}</span>
            </div>
            <div style="font-size: var(--text-sm); color: var(--text-muted);">
              <div><strong>Etkinlik:</strong> ${evTitle}</div>
              <div><strong>Tarih:</strong> ${dateStr}</div>
              <div style="margin-top: var(--space-2); background: var(--bg-subtle); padding: var(--space-2); border-radius: var(--radius-sm); font-style: italic;">"${note}"</div>
            </div>
            ${actionsHtml}
          </div>
        `;
      }).join('');
    }

    document.querySelectorAll('.act-all-app-btn').forEach(btn => {
      btn.addEventListener('click', (e) => {
        const appId = e.currentTarget.getAttribute('data-id');
        const newSt = e.currentTarget.getAttribute('data-st');
        updateAppStatus(appId, newSt, e.currentTarget);
      });
    });
    document.querySelectorAll('.act-view-btn').forEach(btn => {
      btn.addEventListener('click', (e) => {
        const appId = e.currentTarget.getAttribute('data-id');
        openApplicantModal(appId);
      });
    });
  };

  const fillProfileForm = () => {
    document.getElementById('up-org-name').value = org.name || '';
    document.getElementById('up-org-city').value = org.city || '';
    document.getElementById('up-org-web').value = org.website || '';
    document.getElementById('up-org-phone').value = org.phone || '';
    document.getElementById('up-org-address').value = org.address || '';
    document.getElementById('up-org-desc').value = org.description || '';
  };

  const profileForm = document.getElementById('org-profile-update-form');
  if (profileForm) {
    profileForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      const btn = document.getElementById('update-profile-btn');
      btn.disabled = true;
      btn.textContent = 'Kaydediliyor...';
      const payload = {
        name: document.getElementById('up-org-name').value.trim(),
        city: document.getElementById('up-org-city').value.trim(),
        website: document.getElementById('up-org-web').value.trim(),
        phone: document.getElementById('up-org-phone').value.trim(),
        address: document.getElementById('up-org-address').value.trim(),
        description: document.getElementById('up-org-desc').value.trim()
      };
      const res = await window.organizationsService.update(org.id, payload);
      btn.disabled = false;
      btn.textContent = 'Değişiklikleri Kaydet';
      if (res && res.error) {
        window.ui.showToast(res.error, 'error');
      } else {
        window.ui.showToast('STK profiliniz başarıyla güncellendi.', 'success');
        org = { ...org, ...payload };
        document.getElementById('org-header-name').textContent = org.name;
      }
    });
  }

  document.querySelectorAll('.filter-ev-btn').forEach(btn => {
    btn.addEventListener('click', (e) => {
      document.querySelectorAll('.filter-ev-btn').forEach(b => {
        b.classList.remove('active');
        b.style.background = 'transparent';
        b.style.color = 'var(--text-muted)';
        b.style.fontWeight = '600';
      });
      e.currentTarget.classList.add('active');
      e.currentTarget.style.background = 'var(--primary-light)';
      e.currentTarget.style.color = 'var(--primary-main)';
      e.currentTarget.style.fontWeight = '700';
      renderAllEvents(e.currentTarget.getAttribute('data-status'));
    });
  });

  document.querySelectorAll('.filter-app-btn').forEach(btn => {
    btn.addEventListener('click', (e) => {
      document.querySelectorAll('.filter-app-btn').forEach(b => {
        b.classList.remove('active');
        b.style.background = 'transparent';
        b.style.color = 'var(--text-muted)';
        b.style.fontWeight = '600';
      });
      e.currentTarget.classList.add('active');
      e.currentTarget.style.background = 'var(--primary-light)';
      e.currentTarget.style.color = 'var(--primary-main)';
      e.currentTarget.style.fontWeight = '700';
      renderAllApps(e.currentTarget.getAttribute('data-status'));
    });
  });

  const switchTab = (tabName) => {
    document.querySelectorAll('.org-tab-pane').forEach(p => p.style.display = 'none');
    const pane = document.getElementById(`tab-pane-${tabName}`);
    if (pane) pane.style.display = 'block';

    document.querySelectorAll('.org-tab-link').forEach(l => {
      if (l.getAttribute('data-tab') === tabName) {
        l.classList.add('active');
      } else {
        l.classList.remove('active');
      }
    });
  };

  const attachTabLinks = () => {
    document.querySelectorAll('.org-tab-link').forEach(l => {
      l.addEventListener('click', (e) => {
        const t = e.currentTarget.getAttribute('data-tab');
        if (t) {
          e.preventDefault();
          window.location.hash = t;
          switchTab(t);
        }
      });
    });
  };

  attachTabLinks();

  window.addEventListener('hashchange', () => {
    const h = window.location.hash.replace('#', '') || 'overview';
    switchTab(h);
  });

  const initHash = window.location.hash.replace('#', '') || 'overview';
  switchTab(initHash);

  const amModal = document.getElementById('applicant-modal');
  const amClose = document.getElementById('close-applicant-modal');
  const amSkel = document.getElementById('applicant-modal-skeleton');
  const amErr = document.getElementById('applicant-modal-error');
  const amContent = document.getElementById('applicant-modal-content');
  
  if (amClose) {
    amClose.addEventListener('click', () => {
      if (amModal) amModal.style.display = 'none';
    });
  }

  window.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
      if (amModal && amModal.style.display === 'flex') amModal.style.display = 'none';
      if (document.getElementById('edit-event-modal') && document.getElementById('edit-event-modal').style.display === 'flex') document.getElementById('edit-event-modal').style.display = 'none';
    }
  });

  let currentEditEventId = null;
  const editEvModal = document.getElementById('edit-event-modal');
  const editEvClose = document.getElementById('close-edit-event-modal');
  const editEvForm = document.getElementById('edit-event-form');
  const editEvErr = document.getElementById('edit-event-error');
  const editEvBtn = document.getElementById('edit-ev-submit-btn');

  if (editEvClose) {
    editEvClose.addEventListener('click', () => {
      if (editEvModal) editEvModal.style.display = 'none';
    });
  }

  window.openEditEventModal = (evId) => {
    currentEditEventId = evId;
    const ev = allEvents.find(e => e.id == evId);
    if (!ev) return;
    
    document.getElementById('edit-ev-title').value = ev.title || '';
    document.getElementById('edit-ev-category').value = ev.category || '';
    
    // ISO 8601 date comes as "2026-08-02T18:00:00+00:00". Trim it to 16 chars for flatpickr/datetime-local
    const startStr = ev.start_date ? ev.start_date.substring(0, 16) : '';
    const endStr = ev.end_date ? ev.end_date.substring(0, 16) : '';
    
    document.getElementById('edit-ev-start').value = startStr;
    document.getElementById('edit-ev-end').value = endStr;
    
    if (!window._editEvStartPicker) {
      window._editEvStartPicker = flatpickr("#edit-ev-start", { enableTime: true, time_24hr: true, locale: "tr", dateFormat: "Y-m-d\\TH:i", altInput: true, altFormat: "d.m.Y H:i" });
      window._editEvEndPicker = flatpickr("#edit-ev-end", { enableTime: true, time_24hr: true, locale: "tr", dateFormat: "Y-m-d\\TH:i", altInput: true, altFormat: "d.m.Y H:i" });
    } else {
      window._editEvStartPicker.setDate(startStr);
      window._editEvEndPicker.setDate(endStr);
    }

    document.getElementById('edit-ev-city').value = ev.city || '';
    document.getElementById('edit-ev-address').value = ev.address || '';
    document.getElementById('edit-ev-max').value = ev.max_volunteers || '';
    document.getElementById('edit-ev-description').value = ev.description || '';
    document.getElementById('edit-ev-status').value = ev.status || 'draft';
    
    if (editEvErr) editEvErr.style.display = 'none';
    if (editEvModal) editEvModal.style.display = 'flex';
  };

  if (editEvForm) {
    editEvForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      if (!currentEditEventId) return;
      
      if (editEvBtn) {
        editEvBtn.disabled = true;
        editEvBtn.textContent = 'Kaydediliyor...';
      }
      
      const payload = {
        title: document.getElementById('edit-ev-title').value.trim(),
        category: document.getElementById('edit-ev-category').value.trim(),
        start_date: document.getElementById('edit-ev-start').value,
        end_date: document.getElementById('edit-ev-end').value,
        city: document.getElementById('edit-ev-city').value.trim(),
        address: document.getElementById('edit-ev-address').value.trim(),
        description: document.getElementById('edit-ev-description').value.trim(),
        status: document.getElementById('edit-ev-status').value
      };
      
      const maxVol = document.getElementById('edit-ev-max').value;
      if (maxVol) payload.max_volunteers = parseInt(maxVol, 10);
      else payload.max_volunteers = null;
      
      const res = await window.eventsService.update(currentEditEventId, payload);
      
      if (editEvBtn) {
        editEvBtn.disabled = false;
        editEvBtn.textContent = 'Değişiklikleri Kaydet';
      }
      
      if (res && res.error) {
        if (editEvErr) {
          editEvErr.textContent = res.error;
          editEvErr.style.display = 'block';
        }
      } else {
        window.ui.showToast('Etkinlik başarıyla güncellendi.', 'success');
        if (editEvModal) editEvModal.style.display = 'none';
        await loadDashboardData();
      }
    });
  }

  let currentAppId = null;

  window.openApplicantModal = async (appId) => {
    currentAppId = appId;
    if (amModal) amModal.style.display = 'flex';
    if (amSkel) amSkel.style.display = 'flex';
    if (amErr) amErr.style.display = 'none';
    if (amContent) amContent.style.display = 'none';

    const res = await window.recommendationsService.evaluateApplicant({ application_id: Number(appId) });
    if (amSkel) amSkel.style.display = 'none';
    
    if (res && res.error) {
      if (amErr) {
        amErr.textContent = res.error;
        amErr.style.display = 'block';
      }
    } else {
      if (amContent) amContent.style.display = 'block';
      const ev = res.evaluation || {};
      const ap = res.applicant || {};
      document.getElementById('am-name').textContent = ap.full_name || 'İsimsiz Aday';
      document.getElementById('am-city').textContent = ap.city || 'Şehir Belirtilmemiş';
      document.getElementById('am-bio').textContent = ap.bio || 'Hakkında bilgi yok.';
      
      const skillCont = document.getElementById('am-skills');
      if (ap.skills && ap.skills.length > 0) {
        skillCont.innerHTML = ap.skills.map(s => `<span style="background: var(--bg-subtle); padding: 2px 8px; border-radius: 12px; font-size: 11px;">${s}</span>`).join('');
      } else {
        skillCont.innerHTML = '-';
      }
      
      const intCont = document.getElementById('am-interests');
      if (ap.interests && ap.interests.length > 0) {
        intCont.innerHTML = ap.interests.map(i => `<span style="background: var(--bg-subtle); padding: 2px 8px; border-radius: 12px; font-size: 11px;">${i}</span>`).join('');
      } else {
        intCont.innerHTML = '-';
      }
      
      const scoreElem = document.getElementById('am-ai-score');
      if (scoreElem) {
        scoreElem.textContent = `${ev.match_score || 0} / 100`;
        const score = ev.match_score || 0;
        if (score >= 80) scoreElem.style.color = 'var(--primary-main)';
        else if (score >= 50) scoreElem.style.color = 'var(--accent-orange)';
        else scoreElem.style.color = 'var(--accent-red)';
      }
      
      const badgeElem = document.getElementById('am-ai-badge');
      if (badgeElem) {
        if (ev.ai_generated) {
          badgeElem.style.display = 'inline-flex';
        } else {
          badgeElem.style.display = 'none';
        }
      }
      
      const summaryElem = document.getElementById('am-ai-summary');
      if (summaryElem) {
        summaryElem.textContent = ev.summary || 'Değerlendirme yapılamadı.';
      }
      
      const strengthsCont = document.getElementById('am-ai-strengths');
      if (strengthsCont) {
        if (ev.strengths && ev.strengths.length > 0) {
          strengthsCont.innerHTML = ev.strengths.map(s => `<li style="margin-bottom: 4px;">${s}</li>`).join('');
        } else {
          strengthsCont.innerHTML = '<li>Belirgin bir güçlü yön bulunamadı.</li>';
        }
      }
      
      const gapsCont = document.getElementById('am-ai-gaps');
      if (gapsCont) {
        if (ev.gaps && ev.gaps.length > 0) {
          gapsCont.innerHTML = ev.gaps.map(g => `<li style="margin-bottom: 4px;">${g}</li>`).join('');
        } else {
          gapsCont.innerHTML = '<li>Belirgin bir eksiklik tespit edilmedi.</li>';
        }
      }

      const appRecord = allApps.find(a => a.id == appId);
      const approveBtn = document.getElementById('am-approve-btn');
      const rejectBtn = document.getElementById('am-reject-btn');
      
      if (appRecord && appRecord.status !== 'pending') {
        if (approveBtn) approveBtn.parentElement.style.display = 'none';
      } else {
        if (approveBtn) approveBtn.parentElement.style.display = 'flex';
      }
    }
  };

  const amApproveBtn = document.getElementById('am-approve-btn');
  if (amApproveBtn) {
    amApproveBtn.addEventListener('click', async (e) => {
      if (currentAppId) {
        await updateAppStatus(currentAppId, 'approved', e.currentTarget);
        if (amModal) amModal.style.display = 'none';
      }
    });
  }

  const amRejectBtn = document.getElementById('am-reject-btn');
  if (amRejectBtn) {
    amRejectBtn.addEventListener('click', async (e) => {
      if (currentAppId) {
        await updateAppStatus(currentAppId, 'rejected', e.currentTarget);
        if (amModal) amModal.style.display = 'none';
      }
    });
  }

  await loadDashboardData();
});
