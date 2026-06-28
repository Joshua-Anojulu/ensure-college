/* Apply the saved or OS-preferred theme before first paint (no flash), and wire
   the header toggle. Kept as an external file because the site CSP is
   `script-src 'self'` and would block an inline script. */
(function () {
  var KEY = "s4u-theme";
  var saved = null;
  try { saved = localStorage.getItem(KEY); } catch (e) {}
  var theme = saved || (window.matchMedia && window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light");
  document.documentElement.setAttribute("data-theme", theme);

  function syncButton() {
    var b = document.getElementById("theme-toggle");
    if (b) b.setAttribute("aria-pressed", String(document.documentElement.getAttribute("data-theme") === "dark"));
  }

  window.__toggleTheme = function () {
    var next = document.documentElement.getAttribute("data-theme") === "dark" ? "light" : "dark";
    document.documentElement.setAttribute("data-theme", next);
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
