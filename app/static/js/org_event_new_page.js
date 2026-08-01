document.addEventListener('DOMContentLoaded', async () => {
  const meRes = await window.authService.me().catch(() => null);
  const user = meRes && meRes.data && meRes.data.user ? meRes.data.user : (meRes && meRes.user ? meRes.user : null);
  if (!user || user.role !== 'organization') {
    window.ui.showToast('Bu sayfaya erişim için STK yetkilisi olarak oturum açmalısınız.', 'error');
    window.location.href = '/organization/dashboard';
    return;
  }

  const errBox = document.getElementById('wizard-error-box');
  const form = document.getElementById('wizard-form');
  let currentStep = 1;

  const saveDraftToLocal = () => {
    const draft = {
      title: document.getElementById('event-title').value,
      category: document.getElementById('event-category').value,
      description: document.getElementById('event-description').value,
      start_date: document.getElementById('event-start').value,
      end_date: document.getElementById('event-end').value,
      city: document.getElementById('event-city').value,
      address: document.getElementById('event-address').value,
      max_volunteers: document.getElementById('event-max').value,
      requirements: document.getElementById('event-requirements').value
    };
    localStorage.setItem('briva_wizard_draft', JSON.stringify(draft));
  };

  const loadDraftFromLocal = () => {
    const saved = localStorage.getItem('briva_wizard_draft');
    if (saved) {
      try {
        const d = JSON.parse(saved);
        if (d.title) document.getElementById('event-title').value = d.title;
        if (d.category) document.getElementById('event-category').value = d.category;
        if (d.description) document.getElementById('event-description').value = d.description;
        if (d.start_date) document.getElementById('event-start').value = d.start_date;
        if (d.end_date) document.getElementById('event-end').value = d.end_date;
        if (d.city) document.getElementById('event-city').value = d.city;
        if (d.address) document.getElementById('event-address').value = d.address;
        if (d.max_volunteers) document.getElementById('event-max').value = d.max_volunteers;
        if (d.requirements) document.getElementById('event-requirements').value = d.requirements;
      } catch (e) {
        localStorage.removeItem('briva_wizard_draft');
      }
    }
  };

  loadDraftFromLocal();

  const showStep = (stepNum) => {
    document.querySelectorAll('.wizard-pane').forEach(p => p.classList.remove('active'));
    const targetPane = document.getElementById(`pane-step-${stepNum}`);
    if (targetPane) targetPane.classList.add('active');

    document.querySelectorAll('.wizard-step').forEach((st, idx) => {
      st.classList.remove('active', 'completed');
      if (idx + 1 === stepNum) {
        st.classList.add('active');
      } else if (idx + 1 < stepNum) {
        st.classList.add('completed');
      }
    });

    currentStep = stepNum;
    if (errBox) errBox.style.display = 'none';
    saveDraftToLocal();

    if (stepNum === 4) {
      updatePreview();
    }
  };

  const validateStep = (stepNum) => {
    if (stepNum === 1) {
      const t = document.getElementById('event-title').value.trim();
      if (!t) {
        if (errBox) {
          errBox.textContent = 'Lütfen Etkinlik Başlığı alanını doldurun.';
          errBox.style.display = 'block';
        }
        return false;
      }
    } else if (stepNum === 2) {
      const st = document.getElementById('event-start').value;
      if (!st) {
        if (errBox) {
          errBox.textContent = 'Lütfen Başlangıç Tarihi ve Saati alanını seçin.';
          errBox.style.display = 'block';
        }
        return false;
      }
    }
    return true;
  };

  document.querySelectorAll('.wizard-next-btn').forEach(btn => {
    btn.addEventListener('click', (e) => {
      const nxt = parseInt(e.currentTarget.getAttribute('data-next'), 10);
      if (validateStep(currentStep)) {
        showStep(nxt);
        window.scrollTo({ top: 0, behavior: 'smooth' });
      }
    });
  });

  document.querySelectorAll('.wizard-prev-btn').forEach(btn => {
    btn.addEventListener('click', (e) => {
      const prv = parseInt(e.currentTarget.getAttribute('data-prev'), 10);
      showStep(prv);
      window.scrollTo({ top: 0, behavior: 'smooth' });
    });
  });

  const aiBtn = document.getElementById('btn-ai-enhance');
  const aiStatus = document.getElementById('ai-status');
  if (aiBtn) {
    aiBtn.addEventListener('click', async () => {
      const title = document.getElementById('event-title').value.trim();
      const desc = document.getElementById('event-description').value.trim();
      const cat = document.getElementById('event-category').value.trim();

      if (!title || !desc) {
        window.ui.showToast('AI analizi için başlık ve açıklama alanları dolu olmalıdır.', 'warning');
        return;
      }

      aiBtn.disabled = true;
      if (aiStatus) {
        aiStatus.style.display = 'inline';
        aiStatus.textContent = 'Yapay Zeka analiz ediyor...';
      }

      try {
        const payload = { title, description: desc };
        if (cat) payload.category = cat;
        // Check if there is an endpoint for AI analysis. Assuming POST /api/ai/analyze-event
        const res = await window.apiService.post('/ai/analyze-event', payload);
        if (res.error) throw new Error(res.error);
        
        // Populate the description with the improved version if available, or just show the score
        if (res.data && res.data.analysis) {
          if (res.data.analysis.improved_description && res.data.analysis.improved_description.trim() !== '') {
            document.getElementById('event-description').value = res.data.analysis.improved_description;
            saveDraftToLocal();
          }
          
          const feedbackDiv = document.getElementById('ai-feedback');
          const list = document.getElementById('ai-suggestions-list');
          if (feedbackDiv && list) {
             list.innerHTML = '';
             let items = [];
             if (res.data.analysis.concrete_suggestions) items.push(...res.data.analysis.concrete_suggestions.map(s => `<li style="margin-bottom: 4px;">💡 ${s}</li>`));
             if (res.data.analysis.missing_info) items.push(...res.data.analysis.missing_info.map(s => `<li style="margin-bottom: 4px;">⚠️ ${s}</li>`));
             if (res.data.analysis.missing_info_reasoning) items.push(`<li style="margin-bottom: 4px; font-style: italic; color: var(--text-muted);">🤔 ${res.data.analysis.missing_info_reasoning}</li>`);
             if (res.data.analysis.title_suggestion) items.push(`<li style="margin-bottom: 4px;">🎯 <strong>Başlık Önerisi:</strong> ${res.data.analysis.title_suggestion}</li>`);
             if (res.data.analysis.requirements_suggestion) items.push(`<li style="margin-bottom: 4px;">✅ <strong>Gereksinim Önerisi:</strong> ${res.data.analysis.requirements_suggestion}</li>`);
             
             if (items.length > 0) {
                 list.innerHTML = items.join('');
                 feedbackDiv.style.display = 'block';
             } else {
                 feedbackDiv.style.display = 'none';
             }
          }
          
          window.ui.showToast(`AI Analizi Tamamlandı! Kalite Skoru: ${res.data.analysis.quality_score}/100`, 'success');
        }
      } catch (err) {
        window.ui.showToast(err.message || 'AI analizi başarısız oldu.', 'error');
      } finally {
        aiBtn.disabled = false;
        if (aiStatus) {
          aiStatus.style.display = 'none';
          aiStatus.textContent = '';
        }
      }
    });
  }

  const updatePreview = () => {
    document.getElementById('prev-title').textContent = document.getElementById('event-title').value || '-';
    document.getElementById('prev-category').textContent = document.getElementById('event-category').value || '-';

    const st = document.getElementById('event-start').value;
    const en = document.getElementById('event-end').value;
    let datesStr = st ? window.formatDate(st) : '-';
    if (en) datesStr += ` — ${window.formatDate(en)}`;
    document.getElementById('prev-dates').textContent = datesStr;

    const cty = document.getElementById('event-city').value;
    const addr = document.getElementById('event-address').value;
    let locStr = cty || '';
    if (addr) locStr += (locStr ? ` (${addr})` : addr);
    document.getElementById('prev-location').textContent = locStr || '-';

    document.getElementById('prev-max').textContent = document.getElementById('event-max').value ? `${document.getElementById('event-max').value} Kişi` : 'Sınırsız';
    document.getElementById('prev-reqs').textContent = document.getElementById('event-requirements').value || 'Özel gereksinim belirtilmedi.';
    document.getElementById('prev-desc').textContent = document.getElementById('event-description').value || 'Açıklama girilmedi.';
  };

    let currentStatus = 'published';
    
    const draftBtn = document.getElementById('wizard-draft-btn');
    if (draftBtn) {
      draftBtn.addEventListener('click', () => {
        currentStatus = 'draft';
        if (form) form.dispatchEvent(new Event('submit', { cancelable: true, bubbles: true }));
      });
    }

    const submitBtn = document.getElementById('wizard-submit-btn');
    if (submitBtn) {
      submitBtn.addEventListener('click', () => {
        currentStatus = 'published';
      });
    }

  if (form) {
    form.addEventListener('submit', async (e) => {
      e.preventDefault();
      if (!validateStep(1) || !validateStep(2)) {
        return;
      }
      
      const prevSubmitText = submitBtn ? submitBtn.textContent : '';
      const prevDraftText = draftBtn ? draftBtn.textContent : '';
      
      if (currentStatus === 'published' && submitBtn) {
        submitBtn.disabled = true;
        submitBtn.textContent = 'Yayınlanıyor...';
        if (draftBtn) draftBtn.disabled = true;
      } else if (currentStatus === 'draft' && draftBtn) {
        draftBtn.disabled = true;
        draftBtn.textContent = 'Kaydediliyor...';
        if (submitBtn) submitBtn.disabled = true;
      }

      const payload = {
        title: document.getElementById('event-title').value.trim(),
        start_date: document.getElementById('event-start').value,
        status: currentStatus
      };

      const cat = document.getElementById('event-category').value.trim();
      if (cat) payload.category = cat;

      const desc = document.getElementById('event-description').value.trim();
      if (desc) payload.description = desc;

      const en = document.getElementById('event-end').value;
      if (en) payload.end_date = en;

      const cty = document.getElementById('event-city').value.trim();
      if (cty) payload.city = cty;

      const addr = document.getElementById('event-address').value.trim();
      if (addr) payload.address = addr;

      const mx = document.getElementById('event-max').value;
      if (mx) payload.max_volunteers = parseInt(mx, 10);

      const reqs = document.getElementById('event-requirements').value.trim();
      if (reqs) payload.requirements = reqs;

      const res = await window.eventsService.create(payload);
      
      if (submitBtn) {
        submitBtn.disabled = false;
        submitBtn.textContent = prevSubmitText;
      }
      if (draftBtn) {
        draftBtn.disabled = false;
        draftBtn.textContent = prevDraftText;
      }

      if (res && res.error) {
        window.ui.showToast(res.error, 'error');
        if (errBox) {
          errBox.textContent = res.error;
          errBox.style.display = 'block';
        }
      } else {
        localStorage.removeItem('briva_wizard_draft');
        const msg = currentStatus === 'draft' ? 'Etkinliğiniz taslak olarak kaydedildi.' : 'Etkinliğiniz başarıyla yayınlandı!';
        window.ui.showToast(msg, 'success');
        setTimeout(() => {
          window.location.href = '/organization/dashboard#events';
        }, 1200);
      }
    });
  }

  const inputs = form.querySelectorAll('input, textarea');
  inputs.forEach(inp => {
    inp.addEventListener('input', saveDraftToLocal);
  });
});
