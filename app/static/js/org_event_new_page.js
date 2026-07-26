document.addEventListener('DOMContentLoaded', async () => {
  const meRes = await window.authService.me();
  const user = meRes && meRes.user ? meRes.user : null;
  if (!user || user.role !== 'organization') {
    showToast('Bu sayfaya erişim için STK yetkilisi olarak oturum açmalısınız.', 'error');
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

  if (form) {
    form.addEventListener('submit', async (e) => {
      e.preventDefault();
      if (!validateStep(1) || !validateStep(2)) {
        return;
      }
      const submitBtn = document.getElementById('wizard-submit-btn');
      submitBtn.disabled = true;
      submitBtn.textContent = 'Yayınlanıyor ve AI ile Analiz Ediliyor...';

      const payload = {
        title: document.getElementById('event-title').value.trim(),
        start_date: document.getElementById('event-start').value
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
      submitBtn.disabled = false;
      submitBtn.textContent = 'Etkinliği Yayınla';

      if (res && res.error) {
        showToast(res.error, 'error');
        if (errBox) {
          errBox.textContent = res.error;
          errBox.style.display = 'block';
        }
      } else {
        localStorage.removeItem('briva_wizard_draft');
        showToast('Etkinliğiniz başarıyla yayınlandı!', 'success');
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
