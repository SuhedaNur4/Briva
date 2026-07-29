import re

with open("app/static/js/dashboard_page.js", "r", encoding="utf-8") as f:
    content = f.read()

# 1. Update loadDashboard
content = content.replace(
"""  async function loadDashboard() {
    loadUser();
    loadApplications();
    loadRecommendations();
    loadFavorites();
  }""",
"""  async function loadDashboard() {
    loadUser();
    loadApplications();
    // loadRecommendations(); // Artık butona basılınca çağrılacak
    loadFavorites();
    loadGamification();
    loadXpHistory();
    loadLeaderboard();
  }""", 1)

# 2. Add Smart Match Button Listener
content = content.replace(
"""  async function loadRecommendations() {""",
"""  const btnSmartMatch = document.getElementById('btn-smart-match');
  if (btnSmartMatch) {
    btnSmartMatch.addEventListener('click', async () => {
      btnSmartMatch.disabled = true;
      btnSmartMatch.textContent = 'Aranıyor...';
      await loadRecommendations();
      btnSmartMatch.disabled = false;
      btnSmartMatch.textContent = 'Bana Etkinlik Bul';
    });
  }

  async function loadRecommendations() {""", 1)

# 3. Update loadRecommendations matching reasons
content = content.replace(
"""<p style="font-size: var(--text-xs); color: var(--text-muted); margin-bottom: var(--space-4);">İlgi alanlarınız ve beceri kriterlerinizle yüksek uyum gösteriyor.</p>""",
"""<div style="font-size: var(--text-xs); color: var(--text-muted); margin-bottom: var(--space-4); display: flex; flex-direction: column; gap: 4px;">
              ${(rec.evaluation && rec.evaluation.reasons && rec.evaluation.reasons.length > 0) 
                 ? rec.evaluation.reasons.map(r => `<span>✓ ${r}</span>`).join('') 
                 : (rec.details && Object.keys(rec.details).length > 0 
                     ? Object.entries(rec.details).filter(([k,v]) => v && v.length > 0).map(([k,v]) => `<span>✓ ${k === 'matching_skills' ? 'Becerilerinle örtüşüyor' : (k === 'matching_interests' ? 'İlgi alanlarınla örtüşüyor' : (k === 'city_matched' ? 'Konumuna uygun' : (k === 'day_matched' ? 'Müsaitlik gününle uyumlu' : 'Profilinle uyumlu')))}</span>`).join('') 
                     : '<span>✓ Profilinle genel olarak uyumlu</span>')}
              </div>""", 1)

# 4. Append Gamification Logic at the very end, before the last line '});\n'
gamification_code = """
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
          if (gamEmptyText) gamEmptyText.textContent = 'Henüz XP kazanmadınız.';
        }
        return;
      }

      if (gamContent) gamContent.style.display = 'block';
      const levelEl = document.getElementById('gamification-level');
      if (levelEl) levelEl.textContent = gam.level;
      
      const xpEl = document.getElementById('gamification-xp');
      if (xpEl) xpEl.textContent = window.formatNumber(gam.xp) + ' XP';
      
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
            <strong style="color: var(--primary-main); font-size: var(--text-base);">+${item.amount} XP</strong>
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
            <strong style="font-size: var(--text-sm); color: var(--text-muted);">${window.formatNumber(entry.xp)} XP</strong>
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
"""

# Find the last occurrence of "});"
parts = content.rsplit("});", 1)
if len(parts) == 2:
    new_content = parts[0] + gamification_code + "\n});" + parts[1]
    with open("app/static/js/dashboard_page.js", "w", encoding="utf-8") as f:
        f.write(new_content)
else:
    print("Could not find ending '});'")
