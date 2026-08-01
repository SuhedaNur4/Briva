document.addEventListener('DOMContentLoaded', async () => {
  const authButtons = document.getElementById('nav-auth-buttons');
  const userProfile = document.getElementById('nav-user-profile');
  const userGreeting = document.getElementById('nav-user-greeting');

  if (window.apiService && window.apiService.getToken()) {
    if (authButtons) authButtons.style.display = 'none';
    if (userProfile) userProfile.style.display = 'flex';
    
    try {
      const res = await window.authService.me();
      const user = res.data.user || res.data;
      let name = '';
      if (user.role === 'volunteer' && user.volunteer_profile) {
        name = user.volunteer_profile.first_name || user.email.split('@')[0];
        
        // Gamification / XP gösterimi
        const xpBadge = document.getElementById('nav-xp-badge');
        const xpPoints = document.getElementById('nav-xp-points');
        if (xpBadge && xpPoints) {
          xpPoints.textContent = user.volunteer_profile.xp_points || 0;
          xpBadge.style.display = 'flex';
        }
      } else if (user.role === 'organization') {
        name = user.organization?.name || user.email.split('@')[0];
        const dashLink = document.getElementById('nav-dashboard-link');
        if (dashLink) dashLink.href = '/organization/dashboard';
      } else {
        name = user.email.split('@')[0];
      }
      if (userGreeting) userGreeting.textContent = `Hoş geldin, ${name}`;
    } catch (e) {
      if (userGreeting) userGreeting.textContent = `Hoş geldin`;
    }
  } else {
    if (authButtons) authButtons.style.display = 'flex';
    if (userProfile) userProfile.style.display = 'none';
  }
});
