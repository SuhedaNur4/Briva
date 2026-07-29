document.addEventListener('DOMContentLoaded', async () => {
  const gridEl = document.getElementById('events-grid');
  const skeletonEl = document.getElementById('events-skeleton');
  const emptyEl = document.getElementById('events-empty');
  const errorEl = document.getElementById('events-error');
  const activeContainerEl = document.getElementById('active-filters-container');
  const chipsListEl = document.getElementById('filter-chips-list');

  const searchInput = document.getElementById('search-input');
  const cityFilter = document.getElementById('city-filter');
  const categoryFilter = document.getElementById('category-filter');
  const dateFilter = document.getElementById('date-filter');
  const skillFilter = document.getElementById('skill-filter');
  const orgFilter = document.getElementById('org-filter');
  const applyBtn = document.getElementById('apply-filters-btn');
  const clearBtn = document.getElementById('clear-filters-btn');
  const emptyClearBtn = document.getElementById('empty-clear-btn');
  const retryBtn = document.getElementById('retry-load-btn');

  // URL'den ?org= parametresini oku ve org filtresini otomatik set et
  const urlParams = new URLSearchParams(window.location.search);
  const orgFromUrl = urlParams.get('org');
  if (orgFromUrl && orgFilter) orgFilter.value = orgFromUrl;

  let allEvents = [];
  let currentPage = 1;
  let recommendationsMap = {};
  let favoritesSet = new Set();
  const loadMoreBtn = document.getElementById('load-more-btn');
  const loadMoreContainer = document.getElementById('load-more-container');


  function showState(state) {
    if (skeletonEl) skeletonEl.style.display = state === 'skeleton' ? 'grid' : 'none';
    if (gridEl) gridEl.style.display = state === 'grid' ? 'grid' : 'none';
    if (emptyEl) emptyEl.style.display = state === 'empty' ? 'block' : 'none';
    if (errorEl) errorEl.style.display = state === 'error' ? 'block' : 'none';
  }

  async function loadInitialData() {
    showState('skeleton');
    try {
      const token = window.apiService.getToken();
      if (token) {
        try {
          const recRes = await window.recommendationsService.getForMe();
          const recs = recRes.data.recommendations || [];
          recs.forEach(r => recommendationsMap[r.event_id] = r);
        } catch (e) {}
        try {
          const favRes = await window.favoritesService.list();
          const favs = favRes.data.favorites || [];
          favs.forEach(f => favoritesSet.add(f.event_id));
        } catch (e) {}
      }
      await applyFilters(true);
    } catch (error) {
      showState('error');
    }
  }

  async function applyFilters(resetPage = true) {
    if (resetPage) {
      currentPage = 1;
      allEvents = [];
      showState('skeleton');
    }

    let query = (searchInput.value || '').trim();
    const city = (cityFilter.value || '').trim();
    const category = (categoryFilter.value || '').trim();
    const dateVal = dateFilter.value || '';
    const skill = (skillFilter.value || '').trim();

    if (skill) {
       query = query ? `${query} ${skill}` : skill;
    }

    let params = { page: currentPage, per_page: 20 };
    if (query) params.q = query;
    if (city) params.city = city;
    if (category) params.category = category;
    if (dateVal) params.start_after = dateVal + 'T00:00:00';
    // org filter
    const orgId = orgFilter ? (orgFilter.value || '').trim() : '';
    if (orgId) params.org_id = orgId;

    renderChips({ query: searchInput.value.trim(), city, category, dateVal, skill });

    try {
      const eventsRes = await window.eventsService.list(params);
      const events = eventsRes.data.events || [];
      const pagination = eventsRes.data.pagination || {};

      if (resetPage) {
        allEvents = events;
      } else {
        allEvents = allEvents.concat(events);
      }

      renderGrid(allEvents);

      if (loadMoreContainer) {
        if (pagination.page < pagination.pages) {
          loadMoreContainer.style.display = 'block';
        } else {
          loadMoreContainer.style.display = 'none';
        }
      }
    } catch (error) {
      if (resetPage) showState('error');
    }
  }

  if (loadMoreBtn) {
    loadMoreBtn.addEventListener('click', () => {
      currentPage++;
      applyFilters(false);
    });
  }

  function renderChips(filters) {
    chipsListEl.innerHTML = '';
    let hasActive = false;

    if (filters.query) {
      hasActive = true;
      chipsListEl.appendChild(createChip(`Arama: ${filters.query}`, () => {
        searchInput.value = '';
        applyFilters();
      }));
    }
    if (filters.city) {
      hasActive = true;
      chipsListEl.appendChild(createChip(`Şehir: ${filters.city}`, () => {
        cityFilter.value = '';
        applyFilters();
      }));
    }
    if (filters.category) {
      hasActive = true;
      chipsListEl.appendChild(createChip(`Kategori: ${filters.category}`, () => {
        categoryFilter.value = '';
        applyFilters();
      }));
    }
    if (filters.dateVal) {
      hasActive = true;
      chipsListEl.appendChild(createChip(`Tarih: ${window.formatDate(filters.dateVal)}`, () => {
        dateFilter.value = '';
        applyFilters();
      }));
    }
    if (filters.skill) {
      hasActive = true;
      chipsListEl.appendChild(createChip(`Beceri: ${filters.skill}`, () => {
        skillFilter.value = '';
        applyFilters();
      }));
    }

    activeContainerEl.style.display = hasActive ? 'flex' : 'none';
  }

  function createChip(text, onRemove) {
    const chip = document.createElement('span');
    chip.className = 'filter-chip';
    chip.innerHTML = `<span>${text}</span><button type="button" aria-label="Filtreyi kaldır">x</button>`;
    const btn = chip.querySelector('button');
    btn.addEventListener('click', onRemove);
    return chip;
  }

  function renderGrid(events) {
    if (!events.length) {
      showState('empty');
      return;
    }
    gridEl.innerHTML = '';
    events.forEach(event => {
      const rec = recommendationsMap[event.id];
      const isFav = favoritesSet.has(event.id);
      const orgName = event.organization && event.organization.name || 'Sivil Toplum Kuruluşu';
      const isVerified = event.organization && event.organization.is_verified;

      const card = document.createElement('article');
      card.className = 'event-card';

      let matchHtml = '';
      if (rec && rec.total_score > 0) {
        const badgeText = window.formatRecommendationBadge(rec, event.city);
        if (badgeText) {
          matchHtml = `
            <div style="background: var(--bg-surface-alt); color: var(--color-primary); padding: 4px 10px; border-radius: var(--radius-full); font-size: var(--text-xs); font-weight: 600; display: inline-block; margin-bottom: var(--space-2); border: 1px solid var(--border-subtle);">
              Bu etkinlik sana uygun olabilir: ${badgeText}
            </div>
          `;
        }
      }

      const dateStr = window.formatDate(event.start_date);
      const timeStr = window.formatTime(event.start_date);
      const locationStr = event.city ? `${event.city} - ${event.location || ''}` : (event.location || 'Çevrimiçi / Belirtilmemiş');

      card.innerHTML = `
        <div class="event-card-header" style="display: flex; justify-content: space-between; align-items: center; margin-bottom: var(--space-2);">
          <span class="event-category" style="font-size: var(--text-xs); font-weight: 600; color: var(--primary-main);">${event.category || 'Genel'}</span>
          ${matchHtml}
        </div>
        <div class="event-card-body">
          <h2 class="event-title" style="font-size: var(--text-lg); margin-bottom: var(--space-1);">
            <a href="/events/${event.id}" style="color: var(--text-main); text-decoration: none;">${event.title}</a>
          </h2>
          <div style="font-size: var(--text-sm); color: var(--text-muted); margin-bottom: var(--space-4); display: flex; align-items: center; gap: var(--space-2); flex-wrap: wrap;">
            <span style="display: inline-flex; align-items: center; gap: 4px;">
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" style="flex-shrink:0;"><path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/><polyline points="9 22 9 12 15 12 15 22"/></svg>
              ${orgName}
            </span>
            ${isVerified ? '<span style="color: var(--primary-main); font-weight: 700; font-size: var(--text-xs); background: rgba(15,82,56,0.08); padding: 2px 8px; border-radius: 99px; border: 1px solid rgba(15,82,56,0.15);">✓ Doğrulanmış</span>' : ''}
          </div>
          <div style="font-size: var(--text-xs); color: var(--text-muted); display: flex; flex-direction: column; gap: var(--space-1); margin-bottom: var(--space-4); background: var(--bg-subtle); padding: var(--space-3); border-radius: var(--radius-md);">
            <div><strong>Tarih:</strong> ${dateStr} (${timeStr})</div>
            <div><strong>Lokasyon:</strong> ${locationStr}</div>
            <div><strong>Kontenjan:</strong> ${event.quota ? `${event.quota} Gönüllü İhtiyacı` : 'Belirtilmemiş'}</div>
          </div>
        </div>
        <div class="event-card-footer" style="display: flex; justify-content: space-between; align-items: center; border-top: 1px solid var(--border-subtle); padding-top: var(--space-3); gap: var(--space-2);">
          <a href="/events/${event.id}" class="btn btn-primary" style="flex: 1; text-align: center;">Detayları Gör</a>
          <button type="button" class="btn ${isFav ? 'btn-secondary' : 'btn-outline'}" data-fav-id="${event.id}" aria-label="${isFav ? 'Favorilerden çıkar' : 'Favorilere ekle'}">
            ${isFav ? 'Kaydedildi' : 'Kaydet'}
          </button>
        </div>
      `;

      const favBtn = card.querySelector(`[data-fav-id="${event.id}"]`);
      favBtn.addEventListener('click', () => toggleFavorite(event.id, favBtn));

      gridEl.appendChild(card);
    });
    showState('grid');
  }

  async function toggleFavorite(eventId, btnEl) {
    if (!window.apiService.getToken()) {
      window.ui.showToast('Favorilere eklemek için önce giriş yapmalısınız.', 'error');
      setTimeout(() => { window.location.href = '/dashboard'; }, 1500);
      return;
    }
    const isFav = favoritesSet.has(eventId);
    try {
      if (isFav) {
        await window.favoritesService.remove(eventId);
        favoritesSet.delete(eventId);
        btnEl.className = 'btn btn-outline';
        btnEl.textContent = 'Kaydet';
        window.ui.showToast('Etkinlik favorilerden çıkarıldı.');
      } else {
        await window.favoritesService.add(eventId);
        favoritesSet.add(eventId);
        btnEl.className = 'btn btn-secondary';
        btnEl.textContent = 'Kaydedildi';
        window.ui.showToast('Etkinlik favorilere kaydedildi.');
      }
    } catch (error) {
      window.ui.showToast(error.message || 'Favori işlemi başarısız oldu.', 'error');
    }
  }

  function clearAllFilters() {
    searchInput.value = '';
    cityFilter.value = '';
    categoryFilter.value = '';
    dateFilter.value = '';
    skillFilter.value = '';
    applyFilters();
  }

  if (applyBtn) applyBtn.addEventListener('click', applyFilters);
  if (clearBtn) clearBtn.addEventListener('click', clearAllFilters);
  if (emptyClearBtn) emptyClearBtn.addEventListener('click', clearAllFilters);
  if (retryBtn) retryBtn.addEventListener('click', loadInitialData);

  if (searchInput) {
    searchInput.addEventListener('input', () => {
      applyFilters();
    });
  }
  if (cityFilter) cityFilter.addEventListener('change', applyFilters);
  if (categoryFilter) categoryFilter.addEventListener('change', applyFilters);
  if (dateFilter) dateFilter.addEventListener('change', applyFilters);
  if (skillFilter) skillFilter.addEventListener('change', applyFilters);

  loadInitialData();
});
