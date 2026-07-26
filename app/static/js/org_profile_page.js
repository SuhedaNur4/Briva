document.addEventListener('DOMContentLoaded', async () => {
  const pageEl = document.querySelector('.org-profile-page');
  if (!pageEl) return;

  const orgId = pageEl.getAttribute('data-org-id');
  if (!orgId) return;

  const res = await window.organizationsService.getById(orgId);
  const org = res && res.organization ? res.organization : null;

  if (!org) {
    document.getElementById('profile-org-name').textContent = 'Kuruluş Bulunamadı';
    document.getElementById('profile-org-city').textContent = '-';
    document.getElementById('profile-org-desc').textContent = 'Belirtilen kimliğe sahip bir kuruluş profili bulunamadı.';
    return;
  }

  document.getElementById('profile-org-name').textContent = org.name || 'İsimsiz Kuruluş';
  document.getElementById('profile-org-city').textContent = org.city || 'Konum belirtilmedi';
  if (org.is_verified) {
    const vBadge = document.getElementById('profile-org-verified');
    if (vBadge) vBadge.style.display = 'inline-block';
  }

  document.getElementById('profile-org-desc').textContent = org.description || 'Kuruluş hakkında henüz bir açıklama eklenmemiş.';

  const webEl = document.getElementById('profile-org-web');
  if (webEl) {
    webEl.innerHTML = org.website ? `<a href="${org.website}" target="_blank" rel="noopener noreferrer">${org.website}</a>` : '-';
  }
  document.getElementById('profile-org-phone').textContent = org.phone || '-';
  document.getElementById('profile-org-address').textContent = org.address || '-';

  const eventsGrid = document.getElementById('profile-org-events');
  if (eventsGrid) {
    const evList = org.events || [];
    const pubEvents = evList.filter(e => e.status === 'published');
    if (pubEvents.length === 0) {
      eventsGrid.innerHTML = `
        <div style="grid-column: 1 / -1; padding: var(--space-8); text-align: center; background: var(--surface-card); border: 1px solid var(--border-subtle); border-radius: var(--radius-md);">
          <p style="color: var(--text-muted); font-size: var(--text-sm);">Kuruluşun şu an yayında olan aktif bir etkinliği bulunmuyor.</p>
        </div>
      `;
    } else {
      eventsGrid.innerHTML = pubEvents.map(ev => {
        const dateStr = window.formatDate(ev.start_date);
        const loc = ev.city || 'Konum belirtilmedi';
        return `
          <div class="event-card">
            <div class="card-header">
              <span class="event-category">${ev.category || 'Genel'}</span>
              <span class="event-status published">Yayında</span>
            </div>
            <h3 class="event-title">${ev.title}</h3>
            <p class="event-meta">
              <span>${dateStr}</span>
              <span>•</span>
              <span>${loc}</span>
            </p>
            <div class="card-footer" style="justify-content: flex-end;">
              <a href="/events/${ev.id}" class="btn btn-outline btn-sm">Detayları İncele</a>
            </div>
          </div>
        `;
      }).join('');
    }
  }
});
