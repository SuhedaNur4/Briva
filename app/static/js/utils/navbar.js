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
      if (user.role === 'volunteer' && user.volunteer_profile && user.volunteer_profile.first_name) {
        name = user.volunteer_profile.first_name;
      } else if (user.role === 'organization' && user.organization && user.organization.name) {
        name = user.organization.name;
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
