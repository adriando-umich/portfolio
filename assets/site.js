(function () {
  // Credit case chart: builds once when it comes into view
  var chart = document.getElementById('chart');
  if (chart) {
    if ('IntersectionObserver' in window) {
      var seen = new IntersectionObserver(function (entries) {
        if (entries[0].isIntersecting) { chart.classList.add('go'); seen.disconnect(); }
      }, { threshold: 0.4 });
      seen.observe(chart);
    } else { chart.classList.add('go'); }
  }

  // Projects page: filter by tool
  var filter = document.querySelector('.filter');
  if (!filter) return;
  var buttons = Array.prototype.slice.call(filter.querySelectorAll('button'));
  var items = Array.prototype.slice.call(document.querySelectorAll('[data-tools]'));
  var groups = Array.prototype.slice.call(document.querySelectorAll('.group'));
  var empty = document.querySelector('.empty');
  function apply(tool) {
    var shown = 0;
    items.forEach(function (el) {
      var on = !tool || (' ' + el.getAttribute('data-tools') + ' ').indexOf(' ' + tool + ' ') > -1;
      el.hidden = !on;
      if (on) shown += 1;
    });
    groups.forEach(function (g) {
      g.hidden = !g.querySelector('[data-tools]:not([hidden])');
    });
    if (empty) empty.style.display = shown ? 'none' : 'block';
    buttons.forEach(function (b) {
      b.setAttribute('aria-pressed', String((b.getAttribute('data-tool') || '') === (tool || '')));
    });
  }
  buttons.forEach(function (b) {
    b.addEventListener('click', function () { apply(b.getAttribute('data-tool') || ''); });
  });
  var start = (location.hash.match(/^#tool=([a-z]+)$/) || [])[1];
  apply(start || '');
})();
