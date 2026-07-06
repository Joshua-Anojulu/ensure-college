/* Pre-paint theme bootstrap. Loaded synchronously in <head> (CSP forbids
   inline scripts) so the right theme applies before first render. */
(function () {
  var stored = null;
  try {
    stored = localStorage.getItem("theme");
  } catch (err) {
    /* storage unavailable */
  }
  var dark = stored === "dark" || (stored !== "light" && window.matchMedia("(prefers-color-scheme: dark)").matches);
  if (dark) {
    document.documentElement.setAttribute("data-theme", "dark");
    var meta = document.getElementById("theme-color-meta");
    if (meta) meta.setAttribute("content", "#16150f");
  }
})();
