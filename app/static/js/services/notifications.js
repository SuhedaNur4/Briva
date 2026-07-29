class NotificationsService {
  list(unreadOnly = false) {
    const params = unreadOnly ? { unread: 'true' } : {};
    return window.apiService.get('/notifications', params);
  }

  markAsRead(id) {
    return window.apiService.put(`/notifications/${id}/read`);
  }

  markAllAsRead() {
    return window.apiService.put('/notifications/read-all');
  }
}

window.notificationsService = new NotificationsService();

document.addEventListener('DOMContentLoaded', () => {
  const notifContainer = document.getElementById('nav-notifications');
  const notifBtn = document.getElementById('nav-notif-btn');
  const notifBadge = document.getElementById('nav-notif-badge');
  const notifDropdown = document.getElementById('nav-notif-dropdown');
  const notifList = document.getElementById('nav-notif-items');
  const notifSkeleton = document.getElementById('nav-notif-skeleton');
  const notifEmpty = document.getElementById('nav-notif-empty');
  const notifError = document.getElementById('nav-notif-error');
  const notifReadAllBtn = document.getElementById('nav-notif-read-all');

  if (!notifContainer) return;

  function setDropdownState(state) {
    if(notifSkeleton) notifSkeleton.style.display = state === 'loading' ? 'block' : 'none';
    if(notifEmpty) notifEmpty.style.display = state === 'empty' ? 'block' : 'none';
    if(notifError) notifError.style.display = state === 'error' ? 'block' : 'none';
    if(notifList) notifList.style.display = state === 'loaded' ? 'block' : 'none';
    if(notifReadAllBtn) notifReadAllBtn.style.display = state === 'loaded' ? 'block' : 'none';
  }

  async function fetchNotifications() {
    if (!window.apiService.getToken()) return;
    notifContainer.style.display = 'block'; // Show bell if logged in
    try {
      const res = await window.notificationsService.list();
      const count = res.data.unread_count || 0;
      if (count > 0) {
        notifBadge.textContent = count;
        notifBadge.style.display = 'block';
      } else {
        notifBadge.style.display = 'none';
      }
      return res.data.notifications || [];
    } catch (e) {
      console.error(e);
      return null;
    }
  }

  async function openDropdown() {
    const isHidden = notifDropdown.style.display === 'none';
    if (isHidden) {
      notifDropdown.style.display = 'block';
      setDropdownState('loading');
      const items = await fetchNotifications();
      if (!items) {
        setDropdownState('error');
      } else if (items.length === 0) {
        setDropdownState('empty');
      } else {
        notifList.innerHTML = '';
        items.forEach(item => {
          const div = document.createElement('div');
          div.style.padding = 'var(--space-3)';
          div.style.borderBottom = '1px solid var(--border-subtle)';
          if (!item.is_read) {
            div.style.backgroundColor = 'var(--bg-subtle)';
          }
          div.innerHTML = `
            <div style="font-size: var(--text-xs); color: var(--text-muted); margin-bottom: 2px;">${window.formatDate ? window.formatDate(item.created_at) : item.created_at}</div>
            <div style="font-size: var(--text-sm); font-weight: ${item.is_read ? 'normal' : '600'};">${item.message}</div>
          `;
          div.style.cursor = 'pointer';
          div.addEventListener('click', async () => {
             if (!item.is_read) {
                try {
                   await window.notificationsService.markAsRead(item.id);
                   div.style.backgroundColor = 'transparent';
                   div.querySelector('div:nth-child(2)').style.fontWeight = 'normal';
                   fetchNotifications(); // update badge
                } catch(e){}
             }
             if (item.related_event_id) {
               window.location.href = `/events/${item.related_event_id}`;
             }
          });
          notifList.appendChild(div);
        });
        setDropdownState('loaded');
      }
    } else {
      notifDropdown.style.display = 'none';
    }
  }

  if (notifBtn) {
    notifBtn.addEventListener('click', (e) => {
      e.stopPropagation();
      openDropdown();
    });
  }

  if (notifReadAllBtn) {
    notifReadAllBtn.addEventListener('click', async (e) => {
      e.stopPropagation();
      try {
        await window.notificationsService.markAllAsRead();
        notifDropdown.style.display = 'none';
        fetchNotifications();
      } catch(e) {}
    });
  }

  document.addEventListener('click', (e) => {
    if (notifDropdown && notifDropdown.style.display === 'block') {
      if (!notifContainer.contains(e.target)) {
        notifDropdown.style.display = 'none';
      }
    }
  });

  fetchNotifications();
});
