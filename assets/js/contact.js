/* Contact form — hands the message to the visitor's own mail client.
 *
 * There is no backend. SEND folds the four fields into one mailto: URL, so
 * what arrives in the studio inbox reads as a letter — the enquiry type and
 * the sender's name in the subject, the message and a signature in the body
 * — rather than as a dump of form keys.
 *
 * With JavaScript off the form still submits: its action is a plain mailto:
 * and the browser posts the fields as text. This file only makes the result
 * tidy, which is the correct default.
 */
(function () {
  "use strict";

  var form = document.querySelector("[data-mailto]");
  if (!form) return;

  var to = form.getAttribute("data-mailto");
  var note = form.querySelector("[data-note]");

  function value(field) {
    return form.elements[field] ? form.elements[field].value.trim() : "";
  }

  form.addEventListener("submit", function (e) {
    e.preventDefault();

    var kind = form.elements.enquiry;
    kind = kind.options[kind.selectedIndex].text;

    var name = value("name");
    var subject = name ? kind + " — " + name : kind;
    var body = value("message") + "\n\n—\n" + name + "\n" + value("email") + "\n";

    /* mailto: either opens a mail client or does nothing at all, and the page
       cannot tell which. The note says what should happen and repeats the
       address for the visitor whose browser has no mail handler. */
    if (note) note.hidden = false;

    window.location.href = "mailto:" + to +
      "?subject=" + encodeURIComponent(subject) +
      "&body=" + encodeURIComponent(body);
  });
})();
