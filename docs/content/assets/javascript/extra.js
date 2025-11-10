// Custom JavaScript for Tux documentation

// Get the raw Markdown file URL
function getMdFileUrl() {
  // Try to get the edit URL from MkDocs
  const editLink = document.querySelector('a[href*="edit/"]');
  if (editLink && editLink.href) {
    const editUrl = editLink.href;
    try {
      // Convert GitHub edit URL to raw URL
      // From: https://github.com/owner/repo/edit/branch/docs/path/file.md
      // To: https://raw.githubusercontent.com/owner/repo/branch/docs/path/file.md
      return editUrl
        .replace('github.com', 'raw.githubusercontent.com')
        .replace('/edit/', '/');
    } catch (e) {
      console.error('URL conversion failed:', e);
    }
  }
  return null;
}

// Copy page as Markdown functionality
document.addEventListener('DOMContentLoaded', function() {
  setTimeout(() => {
    const viewBtn = document.querySelector('a[title*="View source"]');
    if (viewBtn) {
      const copyBtn = viewBtn.cloneNode(true);
      copyBtn.title = 'Copy page as Markdown';
      copyBtn.id = 'copy-md-btn';

      const icon = copyBtn.querySelector('svg');
      if (icon) {
        icon.innerHTML = '<path d="M19,21H8V7H19M19,5H8A2,2 0 0,0 6,7V21A2,2 0 0,0 8,23H19A2,2 0 0,0 21,21V7A2,2 0 0,0 19,5M16,1H4A2,2 0 0,0 2,3V17H4V3H16V1Z" />';
      }

      copyBtn.addEventListener('click', async function(e) {
        e.preventDefault();

        try {
          const rawUrl = getMdFileUrl();
          if (!rawUrl) throw new Error('Could not determine raw URL');

          const response = await fetch(rawUrl);
          if (!response.ok) throw new Error(`HTTP ${response.status}`);

          const markdown = await response.text();
          await navigator.clipboard.writeText(markdown);

          showToast('Page copied as Markdown!');
        } catch (error) {
          console.error('Copy failed:', error);
          showToast('Failed to copy page', true);
        }
      });

      viewBtn.parentNode.insertBefore(copyBtn, viewBtn.nextSibling);
    }
  }, 500);
});

function showToast(message, isError = false) {
  const toast = document.createElement('div');
  toast.className = `md-toast ${isError ? 'md-toast--error' : 'md-toast--success'}`;
  toast.textContent = message;

  document.body.appendChild(toast);

  setTimeout(() => toast.classList.add('md-toast--show'), 100);
  setTimeout(() => {
    toast.classList.remove('md-toast--show');
    setTimeout(() => document.body.removeChild(toast), 300);
  }, 2000);
}
