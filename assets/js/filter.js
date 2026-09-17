/* Works index filter.
 *
 * Meta-case text, no pills, no animation — the filter only sets hidden on
 * cards. With JavaScript off every work shows, which is the correct default.
 */
(function () {
  "use strict";

  var grid = document.getElementById("works-grid");
  if (!grid) return;
  var buttons = document.querySelectorAll("[data-filter]");

  function apply(cat) {
    var cards = grid.querySelectorAll("[data-cat]");
    for (var i = 0; i < cards.length; i++) {
      cards[i].hidden = !(cat === "all" || cards[i].dataset.cat === cat);
    }
    for (var j = 0; j < buttons.length; j++) {
      buttons[j].setAttribute(
        "aria-pressed", String(buttons[j].dataset.filter === cat));
    }
  }

  for (var k = 0; k < buttons.length; k++) {
    buttons[k].addEventListener("click", function () {
      apply(this.dataset.filter);
    });
  }
})();
