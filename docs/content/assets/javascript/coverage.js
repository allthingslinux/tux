// Coverage Report Theme Sync
// Syncs the parent page's theme with the coverage report iframe
// Includes loader to prevent theme flashing during navigation
(function () {
  "use strict";

  // Create loader element
  function createLoader() {
    const iframe = document.getElementById("coviframe");
    if (!iframe) return null;

    // Find or create container
    let container = document.getElementById("coviframe-container");
    if (!container) {
      // Create container if it doesn't exist
      container = document.createElement("div");
      container.id = "coviframe-container";
      container.style.position = "relative";
      iframe.parentNode.insertBefore(container, iframe);
      container.appendChild(iframe);
    }

    // Check if loader already exists
    let loader = document.getElementById("coverage-loader");
    if (loader) return loader;

    loader = document.createElement("div");
    loader.id = "coverage-loader";
    loader.className = "hidden"; // Start hidden, will be shown when needed
    const spinner = document.createElement("div");
    spinner.className = "coverage-spinner";
    loader.appendChild(spinner);
    container.appendChild(loader);
    return loader;
  }

  // Show loader
  function showLoader() {
    const loader = createLoader();
    if (loader) {
      loader.classList.remove("hidden");
    }
    const iframe = document.getElementById("coviframe");
    if (iframe) {
      iframe.classList.remove("loaded");
    }
  }

  // Hide loader
  function hideLoader() {
    const loader = document.getElementById("coverage-loader");
    if (loader) {
      loader.classList.add("hidden");
    }
    const iframe = document.getElementById("coviframe");
    if (iframe) {
      iframe.classList.add("loaded");
    }
  }

  function syncCoverageTheme() {
    const iframe = document.getElementById("coviframe");
    if (!iframe) return;

    // Get current theme from parent page
    const currentScheme =
      document.body.getAttribute("data-md-color-scheme") || "tokyo-night";

    // Track if theme has been applied
    let themeApplied = false;
    let hideLoaderTimeout = null;

    // Send theme to iframe
    function sendTheme() {
      const scheme =
        document.body.getAttribute("data-md-color-scheme") || "tokyo-night";
      try {
        iframe.contentWindow.postMessage(
          {
            type: "coverage-theme-change",
            scheme: scheme,
          },
          "*"
        );
        themeApplied = true;
        // Don't hide loader here - wait for confirmation from iframe
      } catch (e) {
        // Iframe might not be ready yet, will retry
        console.debug("Coverage theme sync: iframe not ready", e);
      }
    }

    // Show loader when iframe starts loading
    showLoader();

    // Send theme when iframe loads
    iframe.addEventListener("load", function () {
      // Apply theme immediately before content is visible
      try {
        const iframeDoc =
          iframe.contentDocument || iframe.contentWindow.document;
        if (iframeDoc && iframeDoc.body) {
          // Apply theme class immediately to prevent flash
          const scheme =
            document.body.getAttribute("data-md-color-scheme") || "tokyo-night";
          iframeDoc.body.classList.remove(
            "theme-tokyo-night",
            "theme-catppuccin-latte"
          );
          if (scheme === "tokyo-night" || scheme === "catppuccin-latte") {
            iframeDoc.body.classList.add("theme-" + scheme);
          } else {
            iframeDoc.body.classList.add("theme-tokyo-night");
          }
        }
      } catch (e) {
        // Cross-origin, will use postMessage
      }

      // Wait a bit for iframe content to be ready, then send theme
      setTimeout(sendTheme, 50);

      // Inject theme sync script and CSS into iframe
      try {
        const iframeDoc =
          iframe.contentDocument || iframe.contentWindow.document;
        if (iframeDoc && iframeDoc.body) {
          // Inject CSS for theme classes - use style tag to avoid path issues
          if (!iframeDoc.getElementById("coverage-theme-css")) {
            const style = iframeDoc.createElement("style");
            style.id = "coverage-theme-css";
            style.textContent = `
              /* Apply theme immediately to prevent flash */
              body.indexfile,
              body.pyfile {
                transition: background-color 0.2s ease, color 0.2s ease;
              }

              /* Theme classes for iframe theme syncing */
              body.indexfile.theme-tokyo-night,
              body.pyfile.theme-tokyo-night {
                background-color: #1a1b26 !important;
                color: #a9b1d6 !important;
              }

              body.indexfile.theme-catppuccin-latte,
              body.pyfile.theme-catppuccin-latte {
                background-color: #eff1f5 !important;
                color: #4c4f69 !important;
                font-family: "Inter", -apple-system, BlinkMacSystemFont, "Segoe UI", "Roboto", "Helvetica Neue", "Arial", sans-serif !important;
                font-feature-settings: 'liga' 1, 'calt' 1, 'ss02' 1 !important;
                text-rendering: auto !important;
                font-kerning: normal !important;
              }

              /* Light theme (Catppuccin Latte) - Standalone */
              body.indexfile.theme-catppuccin-latte header {
                background: #e6e9ef !important;
                border-bottom: 1px solid #ccd0da !important;
                color: #4c4f69 !important;
                box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05) !important;
              }

              body.indexfile.theme-catppuccin-latte header h1 {
                color: #4c4f69 !important;
              }

              body.indexfile.theme-catppuccin-latte header h1 .pc_cov {
                color: #1e66f5 !important;
              }

              body.indexfile.theme-catppuccin-latte header h2 {
                color: #4c4f69 !important;
              }

              body.indexfile.theme-catppuccin-latte header h2 a.button {
                background: rgba(230, 233, 239, 0.4) !important;
                border: 1px solid #ccd0da !important;
                color: #4c4f69 !important;
              }

              body.indexfile.theme-catppuccin-latte header h2 a.button:hover {
                background: rgba(30, 102, 245, 0.15) !important;
                border-color: #1e66f5 !important;
                color: #1a1d2e !important;
                box-shadow: 0 0.1rem 0.2rem rgba(30, 102, 245, 0.2) !important;
              }

              body.indexfile.theme-catppuccin-latte header h2 a.button.current {
                background: rgba(30, 102, 245, 0.25) !important;
                border: 2px solid #1e66f5 !important;
                color: #1a1d2e !important;
                box-shadow: 0 0.1rem 0.3rem rgba(30, 102, 245, 0.3) !important;
              }

              body.indexfile.theme-catppuccin-latte header p.text {
                color: #5c5f77 !important;
              }

              body.indexfile.theme-catppuccin-latte header p.text a.nav {
                color: #1e66f5 !important;
              }

              body.indexfile.theme-catppuccin-latte header p.text a.nav:hover {
                color: #04a5e5 !important;
              }

              body.indexfile.theme-catppuccin-latte #filter_container {
                color: #4c4f69 !important;
              }

              body.indexfile.theme-catppuccin-latte #filter_container #filter {
                background: rgba(230, 233, 239, 0.9) !important;
                border: 2px solid #ccd0da !important;
                color: #4c4f69 !important;
              }

              body.indexfile.theme-catppuccin-latte #filter_container #filter:focus {
                border-color: #1e66f5 !important;
                box-shadow: 0 0.1rem 0.3rem rgba(30, 102, 245, 0.2) !important;
              }

              body.indexfile.theme-catppuccin-latte #filter_container #filter::placeholder {
                color: #7c7f93 !important;
              }

              body.indexfile.theme-catppuccin-latte #filter_container label {
                color: #5c5f77 !important;
              }

              body.indexfile.theme-catppuccin-latte table.index {
                border: 1px solid #ccd0da !important;
                box-shadow: 0 0.1rem 0.3rem rgba(0, 0, 0, 0.08) !important;
              }

              body.indexfile.theme-catppuccin-latte table.index thead {
                background: #dce0e8 !important;
              }

              body.indexfile.theme-catppuccin-latte table.index th {
                background: #dce0e8 !important;
                color: #4c4f69 !important;
                border-bottom: 2px solid #ccd0da !important;
              }

              body.indexfile.theme-catppuccin-latte table.index th.name {
                color: #1a1d2e !important;
              }

              body.indexfile.theme-catppuccin-latte table.index th.tablehead.grouphead {
                background: rgba(220, 224, 232, 0.8) !important;
                color: #5c5f77 !important;
              }

              body.indexfile.theme-catppuccin-latte table.index tbody tr.region {
                border-bottom: 1px solid rgba(204, 208, 218, 0.5) !important;
              }

              body.indexfile.theme-catppuccin-latte table.index tbody tr.region:hover {
                background: rgba(230, 233, 239, 0.5) !important;
              }

              body.indexfile.theme-catppuccin-latte table.index tbody tr.region td {
                color: #4c4f69 !important;
              }

              body.indexfile.theme-catppuccin-latte table.index tbody tr.region td.name a {
                color: #1e66f5 !important;
              }

              body.indexfile.theme-catppuccin-latte table.index tbody tr.region td.name a:hover {
                color: #04a5e5 !important;
                background-color: rgba(30, 102, 245, 0.15) !important;
                border-radius: 0.2rem !important;
                padding: 0.1em 0.2em !important;
                margin: 0 -0.2em !important;
              }

              body.indexfile.theme-catppuccin-latte table.index tbody tr.region td[data-ratio^="9"],
              body.indexfile.theme-catppuccin-latte table.index tbody tr.region td[data-ratio^="10"] {
                color: #40a02b !important;
              }

              body.indexfile.theme-catppuccin-latte table.index tbody tr.region td[data-ratio^="5"],
              body.indexfile.theme-catppuccin-latte table.index tbody tr.region td[data-ratio^="6"],
              body.indexfile.theme-catppuccin-latte table.index tbody tr.region td[data-ratio^="7"],
              body.indexfile.theme-catppuccin-latte table.index tbody tr.region td[data-ratio^="8"] {
                color: #df8e1d !important;
              }

              body.indexfile.theme-catppuccin-latte table.index tbody tr.region td[data-ratio^="1"],
              body.indexfile.theme-catppuccin-latte table.index tbody tr.region td[data-ratio^="2"],
              body.indexfile.theme-catppuccin-latte table.index tbody tr.region td[data-ratio^="3"],
              body.indexfile.theme-catppuccin-latte table.index tbody tr.region td[data-ratio^="4"] {
                color: #fe640b !important;
              }

              body.indexfile.theme-catppuccin-latte table.index tbody tr.region td[data-ratio^="0"]:not([data-ratio="0 0"]) {
                color: #d20f39 !important;
              }

              body.indexfile.theme-catppuccin-latte main#index {
                color: #4c4f69 !important;
              }

              body.indexfile.theme-catppuccin-latte #help_panel {
                background: rgba(239, 241, 245, 0.95) !important;
                border: 1px solid #ccd0da !important;
                color: #4c4f69 !important;
                box-shadow: 0 0.2rem 0.5rem rgba(0, 0, 0, 0.15) !important;
              }

              body.indexfile.theme-catppuccin-latte #help_panel .legend {
                color: #1a1d2e !important;
              }

              body.indexfile.theme-catppuccin-latte #help_panel kbd {
                background: rgba(220, 224, 232, 0.8) !important;
                border: 1px solid #ccd0da !important;
                color: #4c4f69 !important;
                box-shadow: 0 0.1rem 0.2rem rgba(0, 0, 0, 0.1) !important;
              }

              body.indexfile.theme-catppuccin-latte footer {
                color: #5c5f77 !important;
              }

              body.indexfile.theme-catppuccin-latte footer .content {
                color: #5c5f77 !important;
              }

              body.indexfile.theme-catppuccin-latte #source {
                color: #4c4f69 !important;
              }

              body.indexfile.theme-catppuccin-latte #source pre {
                background: #e6e9ef !important;
                border: 1px solid #ccd0da !important;
                color: #4c4f69 !important;
                box-shadow: 0 0.1rem 0.3rem rgba(0, 0, 0, 0.08) !important;
              }

              body.indexfile.theme-catppuccin-latte #source .annotate {
                color: #5c5f77 !important;
              }

              /* Individual file template theme styles */
              body.pyfile.theme-tokyo-night header {
                background: #16161e !important;
                border-bottom: 1px solid rgba(86, 95, 137, 0.5) !important;
                color: #a9b1d6 !important;
              }

              body.pyfile.theme-catppuccin-latte header {
                background: #e6e9ef !important;
                border-bottom: 1px solid #ccd0da !important;
                color: #4c4f69 !important;
                box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05) !important;
              }

              body.pyfile.theme-catppuccin-latte header h1 {
                color: #4c4f69 !important;
              }

              body.pyfile.theme-catppuccin-latte header h1 .pc_cov {
                color: #1e66f5 !important;
              }

              body.pyfile.theme-catppuccin-latte header h2 {
                color: #4c4f69 !important;
              }

              body.pyfile.theme-catppuccin-latte header p.text {
                color: #5c5f77 !important;
              }

              body.pyfile.theme-catppuccin-latte header h2 button {
                background: rgba(230, 233, 239, 0.4) !important;
                border: 1px solid #ccd0da !important;
                color: #4c4f69 !important;
              }

              body.pyfile.theme-catppuccin-latte header h2 button:hover {
                background: rgba(30, 102, 245, 0.15) !important;
                border-color: #1e66f5 !important;
                color: #1a1d2e !important;
              }

              /* Light theme source code area - Individual File Pages */
              body.pyfile.theme-catppuccin-latte #source {
                background: #e6e9ef !important;
                border: 1px solid #ccd0da !important;
                color: #4c4f69 !important;
                box-shadow: 0 0.1rem 0.3rem rgba(0, 0, 0, 0.08) !important;
              }

              body.pyfile.theme-catppuccin-latte #source p {
                color: #4c4f69 !important;
              }

              body.pyfile.theme-catppuccin-latte #source p .n {
                color: #7c7f93 !important;
              }

              body.pyfile.theme-catppuccin-latte #source p .n a {
                color: #7c7f93 !important;
              }

              body.pyfile.theme-catppuccin-latte #source p .n a:hover {
                color: #1e66f5 !important;
              }

              /* Light theme line backgrounds - More visible */
              body.pyfile.theme-catppuccin-latte #source p.run {
                background: rgba(64, 160, 43, 0.2) !important;
              }

              body.pyfile.theme-catppuccin-latte #source p.mis {
                background: rgba(210, 15, 57, 0.2) !important;
              }

              body.pyfile.theme-catppuccin-latte #source p.exc {
                background: rgba(124, 127, 147, 0.25) !important;
              }

              body.pyfile.theme-catppuccin-latte #source p.par {
                background: rgba(223, 142, 29, 0.2) !important;
              }

              body.pyfile.theme-catppuccin-latte #source p.run2 {
                background: rgba(64, 160, 43, 0.25) !important;
              }

              /* Light theme syntax highlighting - Match Material theme colors */
              body.pyfile.theme-catppuccin-latte #source p .str {
                color: #40a02b !important;
              }

              body.pyfile.theme-catppuccin-latte #source p .key {
                color: #8839ef !important;
              }

              body.pyfile.theme-catppuccin-latte #source p .op {
                color: #04a5e5 !important;
              }

              body.pyfile.theme-catppuccin-latte #source p .nam {
                color: #4c4f69 !important;
              }

              body.pyfile.theme-catppuccin-latte #source p .com {
                color: #7c7f93 !important;
              }

              body.pyfile.theme-catppuccin-latte footer {
                color: #5c5f77 !important;
              }

              body.pyfile.theme-catppuccin-latte footer .content {
                color: #5c5f77 !important;
              }

              body.pyfile.theme-catppuccin-latte footer a.nav {
                color: #1e66f5 !important;
              }

              /* Dark theme source code area - Individual File Pages */
              body.pyfile.theme-tokyo-night #source {
                background: #16161e !important;
                border: 1px solid rgba(86, 95, 137, 0.3) !important;
                box-shadow: 0 0.1rem 0.3rem rgba(0, 0, 0, 0.2) !important;
              }

              body.pyfile.theme-tokyo-night #source p.run {
                background: rgba(158, 206, 106, 0.2) !important;
              }

              body.pyfile.theme-tokyo-night #source p.mis {
                background: rgba(247, 118, 142, 0.25) !important;
              }

              body.pyfile.theme-tokyo-night #source p.exc {
                background: rgba(86, 95, 137, 0.3) !important;
              }

              body.pyfile.theme-tokyo-night #source p.par {
                background: rgba(224, 175, 104, 0.25) !important;
              }

              body.pyfile.theme-tokyo-night #source p.run2 {
                background: rgba(158, 206, 106, 0.25) !important;
              }
            `;
            iframeDoc.head.appendChild(style);
          }

          // Check if script already exists
          if (!iframeDoc.getElementById("coverage-theme-sync")) {
            const script = iframeDoc.createElement("script");
            script.id = "coverage-theme-sync";
            script.textContent = `
              (function() {
                'use strict';
                let loaderHidden = false;

                function applyTheme(scheme) {
                  const body = document.body;
                  if (!body) return;

                  // Remove existing theme classes
                  body.classList.remove('theme-tokyo-night', 'theme-catppuccin-latte');

                  // Add new theme class
                  if (scheme === 'tokyo-night' || scheme === 'catppuccin-latte') {
                    body.classList.add('theme-' + scheme);
                  } else {
                    // Default to dark theme
                    body.classList.add('theme-tokyo-night');
                  }

                  // Notify parent that theme is applied
                  if (!loaderHidden && window.parent !== window) {
                    try {
                      window.parent.postMessage({
                        type: 'coverage-theme-applied',
                        scheme: scheme
                      }, '*');
                      loaderHidden = true;
                    } catch (e) {
                      // Cross-origin, ignore
                    }
                  }
                }

                // Listen for theme changes from parent
                window.addEventListener('message', function(event) {
                  if (event.data && event.data.type === 'coverage-theme-change') {
                    applyTheme(event.data.scheme);
                  }
                });

                // Apply initial theme if available
                if (window.parent !== window) {
                  try {
                    const parentScheme = window.parent.document.body.getAttribute('data-md-color-scheme');
                    if (parentScheme) {
                      applyTheme(parentScheme);
                    }
                  } catch (e) {
                    // Cross-origin or not ready, will get message instead
                  }
                }

                // Handle navigation within coverage report (clicking links)
                document.addEventListener('click', function(e) {
                  const link = e.target.closest('a');
                  if (link && link.href && !link.href.includes('#')) {
                    // Show loader when navigating to a new page
                    if (window.parent !== window) {
                      try {
                        window.parent.postMessage({
                          type: 'coverage-navigation-start'
                        }, '*');
                      } catch (e) {
                        // Cross-origin, ignore
                      }
                    }
                  }
                });

                // Hide loader when page is fully loaded
                if (document.readyState === 'complete') {
                  if (window.parent !== window) {
                    try {
                      window.parent.postMessage({
                        type: 'coverage-theme-applied',
                        scheme: document.body.classList.contains('theme-catppuccin-latte') ? 'catppuccin-latte' : 'tokyo-night'
                      }, '*');
                    } catch (e) {
                      // Cross-origin, ignore
                    }
                  }
                } else {
                  window.addEventListener('load', function() {
                    if (window.parent !== window) {
                      try {
                        window.parent.postMessage({
                          type: 'coverage-theme-applied',
                          scheme: document.body.classList.contains('theme-catppuccin-latte') ? 'catppuccin-latte' : 'tokyo-night'
                        }, '*');
                      } catch (e) {
                        // Cross-origin, ignore
                      }
                    }
                  });
                }
              })();
            `;
            iframeDoc.head.appendChild(script);
          }
        }
      } catch (e) {
        // Cross-origin or iframe not accessible, use postMessage only
        console.debug(
          "Coverage theme sync: cannot inject script, using postMessage only",
          e
        );
      }
    });

    // Listen for messages from iframe
    window.addEventListener("message", function (event) {
      if (event.data && event.data.type === "coverage-theme-applied") {
        // Clear any pending timeout
        if (hideLoaderTimeout) {
          clearTimeout(hideLoaderTimeout);
          hideLoaderTimeout = null;
        }
        // Hide loader after a short delay to ensure smooth transition
        setTimeout(hideLoader, 100);
      } else if (
        event.data &&
        event.data.type === "coverage-navigation-start"
      ) {
        showLoader();
      }
    });

    // Fallback: Hide loader after max wait time if message never arrives
    hideLoaderTimeout = setTimeout(function () {
      console.debug("Coverage loader: Fallback timeout - hiding loader");
      hideLoader();
    }, 3000);

    // Watch for theme changes
    const observer = new MutationObserver(function (mutations) {
      mutations.forEach(function (mutation) {
        if (
          mutation.type === "attributes" &&
          mutation.attributeName === "data-md-color-scheme"
        ) {
          showLoader();

          // Try to apply theme directly to iframe first (if accessible)
          try {
            const iframeDoc =
              iframe.contentDocument || iframe.contentWindow.document;
            if (iframeDoc && iframeDoc.body) {
              const scheme =
                document.body.getAttribute("data-md-color-scheme") ||
                "tokyo-night";
              // Remove existing theme classes
              iframeDoc.body.classList.remove(
                "theme-tokyo-night",
                "theme-catppuccin-latte"
              );
              // Add new theme class
              if (scheme === "tokyo-night" || scheme === "catppuccin-latte") {
                iframeDoc.body.classList.add("theme-" + scheme);
              } else {
                iframeDoc.body.classList.add("theme-tokyo-night");
              }
              // Hide loader after theme is applied
              setTimeout(hideLoader, 200);
            }
          } catch (e) {
            // Cross-origin, need to use postMessage or reload
            console.debug(
              "Coverage theme: Cannot access iframe directly, using reload",
              e
            );

            // Reload iframe to apply theme
            const currentSrc = iframe.src;
            if (currentSrc) {
              // Store a timestamp to force reload
              const separator = currentSrc.includes("?") ? "&" : "?";
              iframe.src =
                currentSrc + separator + "_theme_reload=" + Date.now();

              // Send theme after reload
              const reloadHandler = function () {
                iframe.removeEventListener("load", reloadHandler);
                setTimeout(sendTheme, 150);
              };
              iframe.addEventListener("load", reloadHandler, { once: true });
            } else {
              // Fallback: just send theme
              sendTheme();
            }
          }
        }
      });
    });

    // Observe body for theme attribute changes
    observer.observe(document.body, {
      attributes: true,
      attributeFilter: ["data-md-color-scheme"],
    });

    // Send initial theme
    if (iframe.contentWindow) {
      setTimeout(sendTheme, 500);
    } else {
      // If iframe not ready, show loader and wait
      showLoader();
    }
  }

  // Run on page load
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", syncCoverageTheme);
  } else {
    syncCoverageTheme();
  }

  // Also run on Material's instant navigation
  if (window.document$) {
    window.document$.subscribe(() => {
      setTimeout(syncCoverageTheme, 100);
    });
  }
})();
