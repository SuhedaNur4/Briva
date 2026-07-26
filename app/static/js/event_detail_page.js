document.addEventListener('DOMContentLoaded', async () => {
  const skeletonEl = document.getElementById('detail-skeleton');
  const errorEl = document.getElementById('detail-error');
  const contentEl = document.getElementById('detail-content');

  const evCategory = document.getElementById('ev-category');
  const evStatus = document.getElementById('ev-status');
  const evTitle = document.getElementById('ev-title');
  const evOrgName = document.getElementById('ev-org-name');
  const evVerifiedBadge = document.getElementById('ev-verified-badge');
  const evDatetime = document.getElementById('ev-datetime');
  const evLocation = document.getElementById('ev-location');
  const evQuota = document.getElementById('ev-quota');
  const evDesc = document.getElementById('ev-desc');
  const evSkillsList = document.getElementById('ev-skills-list');
  const evRequirements = document.getElementById('ev-requirements');

  const aiMatchBox = document.getElementById('ai-match-box');
  const aiScoreText = document.getElementById('ai-match-score-text');
  const aiReasonsList = document.getElementById('ai-reasons-list');

  const applyBox = document.getElementById('apply-box');
  const applyBtn = document.getElementById('apply-btn');
  const coverLetterInput = document.getElementById('cover-letter-input');
  const applySuccessBox = document.getElementById('apply-success-box');

  const pathParts = window.location.pathname.split('/').filter(Boolean);
  const eventId = pathParts[pathParts.length - 1];

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

  function showState(state) {
    if (skeletonEl) skeletonEl.style.display = state === 'skeleton' ? 'grid' : 'none';
    if (errorEl) errorEl.style.display = state === 'error' ? 'block' : 'none';
    if (contentEl) contentEl.style.display = state === 'content' ? 'grid' : 'none';
  }

  async function loadEventDetail() {
    showState('skeleton');
    try {
      const res = await window.eventsService.getById(eventId);
      const event = res.data.event || res.data;
      if (!event || !event.id) {
        throw new Error('Etkinlik bulunamadı');
      }
      renderEvent(event);
      loadExplanation(event.id);
      checkExistingApplication(event.id);
      showState('content');
    } catch (error) {
      showState('error');
    }
  }

  function renderEvent(event) {
    evCategory.textContent = event.category || 'GENEL';
    evTitle.textContent = event.title || '-';
    
    if (event.status === 'published') {
      evStatus.className = 'status-badge status-approved';
      evStatus.textContent = 'Aktif Başvuru';
    } else {
      evStatus.className = 'status-badge status-rejected';
      evStatus.textContent = 'Kapandı';
      if (applyBtn) {
        applyBtn.disabled = true;
        applyBtn.textContent = 'Başvuruya Kapalı';
      }
    }

    if (event.is_full && applyBtn) {
      applyBtn.disabled = true;
      applyBtn.textContent = 'Kontenjan Doldu';
    }

    const org = event.organization || {};
    evOrgName.textContent = org.name || 'Sivil Toplum Kuruluşu';
    if (org.is_verified) {
      evVerifiedBadge.style.display = 'inline-block';
    }

    const dateStr = window.formatDate(event.start_date);
    const timeStr = window.formatTime(event.start_date);
    evDatetime.textContent = `${dateStr} - ${timeStr}`;
    evLocation.textContent = event.city ? `${event.city} | ${event.location || ''}` : (event.location || 'Çevrimiçi');
    evQuota.textContent = event.quota ? `${event.quota} Gönüllü` : 'Belirtilmemiş';

    evDesc.textContent = event.description || 'Açıklama belirtilmemiş.';
    evRequirements.textContent = event.requirements || 'Özel bir katılım gereksinimi belirtilmemiş.';

    evSkillsList.innerHTML = '';
    const skills = (event.requirements || '').split(',').map(s => s.trim()).filter(Boolean);
    if (skills.length) {
      skills.forEach(skill => {
        const chip = document.createElement('span');
        chip.style.background = 'var(--bg-subtle)';
        chip.style.border = '1px solid var(--border-subtle)';
        chip.style.padding = '4px 10px';
        chip.style.borderRadius = 'var(--radius-full)';
        chip.style.fontSize = 'var(--text-xs)';
        chip.style.fontWeight = '600';
        chip.textContent = skill;
        evSkillsList.appendChild(chip);
      });
    } else {
      evSkillsList.innerHTML = '<span style="color: var(--text-muted); font-size: var(--text-sm);">Özel beceri şartı aranmıyor.</span>';
    }
  }

  async function loadExplanation(id) {
    if (!window.apiService.getToken()) {
      aiScoreText.textContent = 'Oturum Açılmadı';
      aiReasonsList.innerHTML = '<li style="font-size: var(--text-xs); color: var(--text-muted);">Uygunluk analizini görmek için giriş yapın.</li>';
      return;
    }
    try {
      const res = await window.recommendationsService.explain(id, {});
      const exp = res.data.explanation || {};
      const totalScore = exp.total_score !== undefined ? exp.total_score : 0;
      const details = exp.matching_details || {};

      const badgeText = window.formatRecommendationBadge(exp, '');
      aiScoreText.textContent = badgeText ? `Bu etkinlik sana uygun olabilir: ${badgeText}` : 'Sana Uygun Fırsat';
      aiReasonsList.innerHTML = '';

      let hasReasons = false;
      if (details.city_matched) {
        hasReasons = true;
        addReason('Konumuna yakın (Şehrinle eşleşiyor)');
      }
      if (details.matching_interests && details.matching_interests.length) {
        hasReasons = true;
        addReason(`İlgi alanlarınla örtüşüyor (${details.matching_interests.join(', ')})`);
      }
      if (details.matching_skills && details.matching_skills.length) {
        hasReasons = true;
        addReason(`Beceri setinle uyumlu (${details.matching_skills.join(', ')})`);
      }
      if (details.day_matched) {
        hasReasons = true;
        addReason('Uygunluk zamanlarınla örtüşüyor');
      }

      if (!hasReasons) {
        addReason('Bu etkinlik genel profil kriterlerinize temel düzeyde uyum sağlamaktadır.');
      }
    } catch (e) {
      aiScoreText.textContent = 'Analiz Edilemedi';
      aiReasonsList.innerHTML = '<li style="font-size: var(--text-xs); color: var(--text-muted);">Öneri motoru verisine ulaşılamadı.</li>';
    }
  }

  function addReason(text) {
    const li = document.createElement('li');
    li.style.fontSize = 'var(--text-xs)';
    li.style.color = 'var(--text-main)';
    li.style.display = 'flex';
    li.style.alignItems = 'center';
    li.style.gap = 'var(--space-2)';
    li.innerHTML = `<span style="width: 6px; height: 6px; background: var(--primary-main); border-radius: 50%; display: inline-block;"></span><span>${text}</span>`;
    aiReasonsList.appendChild(li);
  }

  async function checkExistingApplication(id) {
    if (!window.apiService.getToken()) return;
    try {
      const res = await window.applicationsService.getMy();
      const apps = res.data.applications || [];
      const existing = apps.find(a => Number(a.event_id) === Number(id));
      if (existing) {
        if (applyBox) applyBox.style.display = 'none';
        if (applySuccessBox) applySuccessBox.style.display = 'block';
      }
    } catch (e) {
    }
  }

  if (applyBtn) {
    applyBtn.addEventListener('click', async () => {
      if (!window.apiService.getToken()) {
        showToast('Başvuru yapmak için önce giriş yapmalısınız.', 'error');
        setTimeout(() => { window.location.href = '/dashboard'; }, 1500);
        return;
      }

      const coverLetter = (coverLetterInput.value || '').trim();
      applyBtn.disabled = true;
      const originalText = applyBtn.textContent;
      applyBtn.textContent = 'Başvuruluyor...';

      try {
        await window.eventsService.apply(eventId, coverLetter);
        showToast('Başvurun alındı.');
        if (applyBox) applyBox.style.display = 'none';
        if (applySuccessBox) applySuccessBox.style.display = 'block';
      } catch (error) {
        if (error.status === 409) {
          showToast('Bu etkinliğe zaten başvurdunuz.', 'error');
          if (applyBox) applyBox.style.display = 'none';
          if (applySuccessBox) applySuccessBox.style.display = 'block';
        } else {
          showToast(error.message || 'Başvuru sırasında bir hata oluştu.', 'error');
          applyBtn.disabled = false;
          applyBtn.textContent = originalText;
        }
      }
    });
  }

  loadEventDetail();
});
