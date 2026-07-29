/**
 * personality_test.js — Biva Kişilik Testi Frontend Mantığı
 *
 * - 15 soruyu yönetir
 * - Cevapları toplar
 * - POST /api/quiz/result ile Smart-Match önerileri alır
 * - Sonuçları güzel bir şekilde gösterir
 */
(function () {
  'use strict';

  const TOTAL_QUESTIONS = 15;

  // Cevap deposu
  const answers = {};
  // Multi-select deposu (q14)
  const multiAnswers = { q14: new Set() };

  let currentQuestion = 1;

  // DOM hazır olunca başlat
  document.addEventListener('DOMContentLoaded', init);

  function init() {
    attachOptionListeners();
    attachNextListeners();
    attachCityInput();
    updateProgress();
  }

  // ============================
  // OPTION SEÇME MANTIĞI
  // ============================
  function attachOptionListeners() {
    document.querySelectorAll('.quiz-option').forEach(opt => {
      opt.addEventListener('click', function () {
        const qKey = this.dataset.q;
        const val = this.dataset.v;
        const isMulti = this.dataset.multi === 'true';

        if (isMulti) {
          handleMultiSelect(this, qKey, val);
        } else {
          handleSingleSelect(this, qKey, val);
        }
      });
    });
  }

  function handleSingleSelect(el, qKey, val) {
    // Aynı sorudaki diğer seçimleri kaldır
    document.querySelectorAll(`.quiz-option[data-q="${qKey}"]`).forEach(o => o.classList.remove('selected'));
    el.classList.add('selected');
    answers[qKey] = val;
    // Next butonunu aktif et
    const qNum = el.closest('.quiz-question-wrap').dataset.q;
    enableNextBtn(qNum);
  }

  function handleMultiSelect(el, qKey, val) {
    el.classList.toggle('selected');
    if (multiAnswers[qKey].has(val)) {
      multiAnswers[qKey].delete(val);
    } else {
      multiAnswers[qKey].add(val);
    }
    // Multi-select her zaman geçebilir (0 seçim de OK)
    // next buton zaten disabled değil
  }

  // ============================
  // ŞEHİR GİRİŞİ
  // ============================
  function attachCityInput() {
    const cityInput = document.getElementById('q11-city');
    if (!cityInput) return;
    cityInput.addEventListener('input', function () {
      answers['q11_city'] = this.value.trim().toLowerCase();
    });
  }

  // ============================
  // NEXT BUTON MANTIĞI
  // ============================
  function attachNextListeners() {
    for (let i = 1; i <= TOTAL_QUESTIONS; i++) {
      const btn = document.getElementById(`next-${i}`);
      if (!btn) continue;
      btn.addEventListener('click', () => goNext(i));
    }
  }

  function enableNextBtn(qNum) {
    const btn = document.getElementById(`next-${qNum}`);
    if (btn) btn.disabled = false;
  }

  function goNext(fromQ) {
    if (fromQ === TOTAL_QUESTIONS) {
      submitQuiz();
      return;
    }
    showQuestion(fromQ + 1);
  }

  window.goBack = function (fromQ) {
    if (fromQ <= 1) return;
    showQuestion(fromQ - 1);
  };

  function showQuestion(num) {
    // Mevcut soruyu gizle
    document.querySelectorAll('.quiz-question-wrap').forEach(el => el.classList.remove('active'));
    // Yeni soruyu göster
    const target = document.querySelector(`.quiz-question-wrap[data-q="${num}"]`);
    if (target) {
      target.classList.add('active');
      // Animasyonu sıfırla
      target.style.animation = 'none';
      target.offsetHeight; // reflow
      target.style.animation = '';
    }
    currentQuestion = num;
    updateProgress();
  }

  function updateProgress() {
    const pct = Math.round(((currentQuestion - 1) / TOTAL_QUESTIONS) * 100);
    const fill = document.getElementById('quiz-progress');
    const label = document.getElementById('quiz-progress-label');
    if (fill) fill.style.width = pct + '%';
    if (label) label.textContent = `Soru ${currentQuestion} / ${TOTAL_QUESTIONS}`;
  }

  // ============================
  // QUIZ GÖNDERİMİ
  // ============================
  async function submitQuiz() {
    // Multi-select cevapları ekle
    const finalAnswers = Object.assign({}, answers);
    if (multiAnswers.q14.size > 0) {
      // İlk seçimi main, diğerleri ek olarak
      const vals = Array.from(multiAnswers.q14);
      finalAnswers['q14'] = vals[0];
      if (vals.length > 1) {
        finalAnswers['q14_extra'] = vals.slice(1).join(',');
      }
    }

    // Quiz body'yi gizle, loading göster
    document.getElementById('quiz-body').style.display = 'none';
    document.getElementById('quiz-loading').classList.add('visible');

    try {
      // JWT varsa dahil et
      const token = localStorage.getItem('briva_access_token') || sessionStorage.getItem('briva_access_token');
      const headers = { 'Content-Type': 'application/json' };
      if (token) headers['Authorization'] = `Bearer ${token}`;

      const res = await fetch('/api/quiz/result', {
        method: 'POST',
        headers,
        body: JSON.stringify({
          answers: finalAnswers,
          update_profile: true
        })
      });

      if (!res.ok) throw new Error('API hatası');
      const data = await res.json();
      showResults(data, finalAnswers);
    } catch (err) {
      // Hata durumunda sade bir mesaj göster
      document.getElementById('quiz-loading').classList.remove('visible');
      document.getElementById('quiz-body').style.display = 'block';
      showQuestion(TOTAL_QUESTIONS);
      alert('Sonuçlar yüklenirken bir sorun oluştu. Lütfen tekrar deneyin.');
    }
  }

  // ============================
  // SONUÇ GÖSTERİMİ
  // ============================
  function showResults(data, finalAnswers) {
    document.getElementById('quiz-loading').classList.remove('visible');

    const resultsEl = document.getElementById('quiz-results');
    const insightsEl = document.getElementById('results-insights');
    const recsEl = document.getElementById('results-recs');

    // İlgi alanlarını göster (Insights)
    const interests = data.user_context?.interests || [];
    
    const categoryInsights = {
      'çevre': { icon: '🌍', title: 'Çevre', desc: 'İklim değişikliği ve doğa koruma projeleri senin için öne çıkıyor. Doğaya doğrudan katkı sağlayacağın etkinlikler sana uygun.' },
      'eğitim': { icon: '📚', title: 'Eğitim', desc: 'Bilgi paylaşımı ve başkalarının öğrenmesine destek olabileceğin, fırsat eşitliği odaklı etkinlikler tam sana göre.' },
      'sosyal destek': { icon: '🤝', title: 'Sosyal Etki', desc: 'Topluma doğrudan dokunan, dezavantajlı gruplara yardım edebileceğin sosyal destek projelerine yatkınsın.' },
      'hayvan hakları': { icon: '🐾', title: 'Hayvan Hakları', desc: 'Can dostlarımızın yaşam haklarını savunmak ve onlara bakım sağlamak senin için önemli bir motivasyon kaynağı.' }
    };

    if (insightsEl) {
      insightsEl.innerHTML = '';
      if (interests.length) {
        interests.forEach(interest => {
          const cat = categoryInsights[interest.toLowerCase()] || { icon: '✨', title: interest.charAt(0).toUpperCase() + interest.slice(1), desc: 'Bu alandaki etkinlikler beceri ve ilgi alanlarınla örtüşüyor.' };
          const div = document.createElement('div');
          div.style.padding = '12px 16px';
          div.style.background = 'white';
          div.style.border = '1px solid var(--border-subtle)';
          div.style.borderRadius = 'var(--radius-md)';
          div.style.marginBottom = '8px';
          div.innerHTML = `
            <strong style="display: flex; align-items: center; gap: 8px; font-size: 1rem; color: var(--text-main); margin-bottom: 4px;">
              <span>${cat.icon}</span> ${cat.title}
            </strong>
            <p style="margin: 0; font-size: 0.9rem; color: var(--text-muted); line-height: 1.4;">${cat.desc}</p>
          `;
          insightsEl.appendChild(div);
        });
      } else {
        insightsEl.innerHTML = '<p style="color: var(--text-muted); font-size: 0.9rem;">Genel gönüllülük etkinliklerine uyum sağlayabilecek esnek bir profilin var.</p>';
      }
    }

    // Önerileri göster
    const recs = data.recommendations || [];
    recsEl.innerHTML = '';
    if (recs.length === 0) {
      recsEl.innerHTML = '<p style="color: var(--text-muted); font-size: 0.9rem; text-align: center; padding: 16px;">Profiline uygun etkinlikler yakında eklenecek. Tüm etkinliklere göz atabilirsin!</p>';
    } else {
      recs.slice(0, 4).forEach(rec => {
        const card = document.createElement('div');
        card.className = 'quiz-rec-card';
        const orgName = rec.organization?.name || 'Sivil Toplum Kuruluşu';
        const city = rec.city ? `${rec.city} · ` : '';
        card.innerHTML = `
          <div>
            <h3>${escapeHtml(rec.title)}</h3>
            <p>${city}${escapeHtml(orgName)} · ${escapeHtml(rec.category || 'Genel')}</p>
          </div>
          <a href="/events/${rec.id}" class="quiz-rec-link">İncele</a>
        `;
        recsEl.appendChild(card);
      });
    }

    // Profil güncellendiyse mesaj göster
    if (data.profile_updated) {
      const descEl = document.getElementById('results-desc');
      if (descEl) descEl.textContent = 'Seni biraz daha tanıdık. Profil ilgi alanlarını da cevaplarına göre güncelledik!';
    }

    resultsEl.classList.add('visible');

    // Progress: 100%
    const fill = document.getElementById('quiz-progress');
    const label = document.getElementById('quiz-progress-label');
    if (fill) fill.style.width = '100%';
    if (label) label.textContent = 'Tamamlandı!';
  }

  function escapeHtml(str) {
    if (!str) return '';
    return String(str)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;');
  }
})();
