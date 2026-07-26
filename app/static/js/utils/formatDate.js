function formatDate(dateString, options = {}) {
  if (!dateString) return '-';
  try {
    const date = new Date(dateString);
    if (isNaN(date.getTime())) return dateString;
    const defaultOptions = {
      day: 'numeric',
      month: 'long',
      year: 'numeric',
      ...options
    };
    return new Intl.DateTimeFormat('tr-TR', defaultOptions).format(date);
  } catch (error) {
    return dateString;
  }
}

function formatTime(dateString) {
  if (!dateString) return '-';
  try {
    const date = new Date(dateString);
    if (isNaN(date.getTime())) return '-';
    return new Intl.DateTimeFormat('tr-TR', { hour: '2-digit', minute: '2-digit' }).format(date);
  } catch (error) {
    return '-';
  }
}

window.formatDate = formatDate;
window.formatTime = formatTime;
