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

// Mermaid Theme Toggle Handler
// Automatically reloads the page when switching between light/dark themes
// This ensures Mermaid diagrams update to match the new color scheme

// document.addEventListener('DOMContentLoaded', function () {
//   // Get the palette toggle elements
//   const paletteToggle1 = document.getElementById('__palette_1'); // Dark mode toggle
//   const paletteToggle2 = document.getElementById('__palette_2'); // Light mode toggle

//   // Add event listeners to reload page on theme change
//   if (paletteToggle1) {
//     paletteToggle1.addEventListener('change', function () {
//       // Small delay to ensure theme change is processed
//       setTimeout(() => {
//         location.reload();
//       }, 100);
//     });
//   }

//   if (paletteToggle2) {
//     paletteToggle2.addEventListener('change', function () {
//       // Small delay to ensure theme change is processed
//       setTimeout(() => {
//         location.reload();
//       }, 100);
//     });
//   }
// });


// Copy page as Markdown functionality - DISABLED due to layout shift issues
// TODO: Re-enable when layout shift can be prevented

/*
// Function to add copy button
function addCopyButton() {
  // Remove existing copy button if it exists (for navigation updates)
  const existingBtn = document.getElementById('copy-md-btn');
  if (existingBtn) {
    existingBtn.remove();
  }

  const viewBtn = document.querySelector('a[title*="View source"]');
  if (viewBtn && !document.getElementById('copy-md-btn')) {
    const copyBtn = viewBtn.cloneNode(true);
    copyBtn.title = 'Copy page as Markdown';
    copyBtn.id = 'copy-md-btn';
    copyBtn.setAttribute('aria-label', 'Copy page as Markdown');

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

    // Insert button immediately to prevent layout shift
    viewBtn.parentNode.insertBefore(copyBtn, viewBtn.nextSibling);
  }
}

// Copy page as Markdown functionality
// Handle both initial load and Material's instant navigation
document.addEventListener('DOMContentLoaded', function() {
  // Add button on initial load
  requestAnimationFrame(() => {
    addCopyButton();
  });
});

// Hook into Material's instant navigation events
// Material for MkDocs fires 'navigation' event on page changes
document.addEventListener('navigation', function() {
  // Small delay to ensure DOM is updated after navigation
  requestAnimationFrame(() => {
    setTimeout(() => {
      addCopyButton();
    }, 100);
  });
});

// Also listen for app ready event (Material's app object)
if (typeof app !== 'undefined' && app.ready) {
  app.ready().then(() => {
    addCopyButton();
  });
}

// Fallback: Use MutationObserver to watch for content changes
// This catches navigation even if events don't fire
const observer = new MutationObserver(function(mutations) {
  // Check if action buttons area changed
  const hasActionButtons = document.querySelector('a[title*="View source"]');
  const hasCopyButton = document.getElementById('copy-md-btn');

  if (hasActionButtons && !hasCopyButton) {
    requestAnimationFrame(() => {
      addCopyButton();
    });
  }
});

// Start observing when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
  const contentInner = document.querySelector('.md-content__inner');
  if (contentInner) {
    observer.observe(contentInner, {
      childList: true,
      subtree: true
    });
  }
});
*/

// function showToast(message, isError = false) {
//   const toast = document.createElement('div');
//   toast.className = `md-toast ${isError ? 'md-toast--error' : 'md-toast--success'}`;
//   toast.textContent = message;

//   document.body.appendChild(toast);

//   setTimeout(() => toast.classList.add('md-toast--show'), 100);
//   setTimeout(() => {
//     toast.classList.remove('md-toast--show');
//     setTimeout(() => document.body.removeChild(toast), 300);
//   }, 2000);
// }
