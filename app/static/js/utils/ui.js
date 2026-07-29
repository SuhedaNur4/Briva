class UIUtils {
  showToast(message, type = 'success') {
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

  showState(state, elements = {}) {
    // elements: { skeleton: DOMElement, content: DOMElement, empty: DOMElement, error: DOMElement }
    if (elements.skeleton) {
      elements.skeleton.style.display = state === 'skeleton' ? (elements.skeletonDisplay || 'block') : 'none';
    }
    if (elements.content) {
      elements.content.style.display = state === 'content' ? (elements.contentDisplay || 'block') : 'none';
    }
    if (elements.empty) {
      elements.empty.style.display = state === 'empty' ? (elements.emptyDisplay || 'block') : 'none';
    }
    if (elements.error) {
      elements.error.style.display = state === 'error' ? (elements.errorDisplay || 'block') : 'none';
    }
  }
}

window.ui = new UIUtils();
