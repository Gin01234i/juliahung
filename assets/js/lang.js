/* Bilingual switch.
 *
 * The visibility rules live in site.css and key off data-lang on <html>,
 * which is hard-coded to "en" in the markup. This file only changes that
 * attribute, so the page renders correctly before the script runs and stays
 * correct if it never does. Nothing else on the site depends on JavaScript.
 */
(function () {
  "use strict";

  var KEY = "jh-lang";
  var root = document.documentElement;

  function read() {
    try { return localStorage.getItem(KEY); } catch (e) { return null; }
  }

  function apply(lang) {
    root.setAttribute("data-lang", lang);
    var buttons = document.querySelectorAll("[data-set-lang]");
    for (var i = 0; i < buttons.length; i++) {
      buttons[i].setAttribute(
        "aria-pressed", String(buttons[i].dataset.setLang === lang));
    }
  }

  var saved = read();
  if (saved === "zh" || saved === "en") apply(saved);

  document.addEventListener("click", function (e) {
    var btn = e.target.closest ? e.target.closest("[data-set-lang]") : null;
    if (!btn) return;
    var lang = btn.dataset.setLang;
    apply(lang);
    try { localStorage.setItem(KEY, lang); } catch (err) { /* private mode */ }
  });
})();
