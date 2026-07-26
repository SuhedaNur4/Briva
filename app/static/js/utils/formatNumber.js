function formatNumber(num) {
  if (num === null || num === undefined || isNaN(num)) return '0';
  return new Intl.NumberFormat('tr-TR').format(num);
}

function formatPercent(num) {
  if (num === null || num === undefined || isNaN(num)) return '%0';
  return `%${Math.round(num)}`;
}

function formatRecommendationBadge(rec, evCity) {
  if (!rec) return '';
  const details = rec.details || rec.matching_details || rec.breakdown || {};
  const parts = [];
  if (details.matching_interests && details.matching_interests.length > 0) {
    parts.push('İlgi alanlarınla örtüşüyor');
  }
  if (details.city_matched && details.city_matched.length > 0) {
    parts.push(`${details.city_matched[0]}'da`);
  } else if (evCity) {
    parts.push(`${evCity}'da`);
  }
  if (details.day_matched && details.day_matched.length > 0) {
    parts.push(`${details.day_matched[0]} uygunluğun var`);
  }
  if (details.matching_skills && details.matching_skills.length > 0) {
    parts.push('Becerilerinle eşleşiyor');
  }
  if (parts.length === 0) {
    if (rec.total_score > 0) {
      return 'Sana uygun etkinlik fırsatı';
    }
    return '';
  }
  return parts.join(' · ');
}

window.formatNumber = formatNumber;
window.formatPercent = formatPercent;
window.formatRecommendationBadge = formatRecommendationBadge;

