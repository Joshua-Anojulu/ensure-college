/* Apply the saved or OS-preferred theme before first paint (no flash), keep the
   mobile browser-chrome color (theme-color meta) in sync, and wire the header
   toggle. Kept as an external file because the site CSP is `script-src 'self'`
   and would block an inline script. */
(function () {
  var KEY = "s4u-theme";
  var CHROME = { light: "#f5f7fb", dark: "#0b0e16" };

  function apply(theme) {
    document.documentElement.setAttribute("data-theme", theme);
    var meta = document.getElementById("theme-color-meta");
    if (meta) meta.setAttribute("content", CHROME[theme] || CHROME.light);
  }

  function syncButton() {
    var b = document.getElementById("theme-toggle");
    if (b) b.setAttribute("aria-pressed", String(document.documentElement.getAttribute("data-theme") === "dark"));
  }

  var saved = null;
  try { saved = localStorage.getItem(KEY); } catch (e) {}
  apply(saved || (window.matchMedia && window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light"));

  window.__toggleTheme = function () {
    var next = document.documentElement.getAttribute("data-theme") === "dark" ? "light" : "dark";
    apply(next);
    try { localStorage.setItem(KEY, next); } catch (e) {}
    syncButton();
  };

  document.addEventListener("DOMContentLoaded", function () {
    var b = document.getElementById("theme-toggle");
    if (b) {
      syncButton();
      b.addEventListener("click", window.__toggleTheme);
    }
  });
})();
