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

  // Board deck: scale the 1280 x 720 slides to the stage, and step through them
  Array.prototype.forEach.call(document.querySelectorAll('.deck'), function (deck) {
    var stage = deck.querySelector('.stage');
    var slides = Array.prototype.slice.call(stage.querySelectorAll('.slide'));
    var prev = deck.querySelector('.prev'), next = deck.querySelector('.next');
    var count = deck.querySelector('.count'), full = deck.querySelector('.full');
    var at = 0;
    function fit() {
      var fs = document.fullscreenElement === stage;
      var k = fs ? Math.min(window.innerWidth / 1280, window.innerHeight / 720) : stage.clientWidth / 1280;
      slides.forEach(function (s) {
        s.style.transform = 'scale(' + k + ')';
        s.style.left = fs ? (window.innerWidth - 1280 * k) / 2 + 'px' : '0';
        s.style.top = fs ? (window.innerHeight - 720 * k) / 2 + 'px' : '0';
      });
    }
    function show(i) {
      at = Math.max(0, Math.min(slides.length - 1, i));
      slides.forEach(function (s, n) { s.classList.toggle('on', n === at); });
      count.textContent = (at + 1) + ' / ' + slides.length;
      prev.disabled = at === 0;
      next.disabled = at === slides.length - 1;
    }
    prev.addEventListener('click', function () { show(at - 1); });
    next.addEventListener('click', function () { show(at + 1); });
    stage.addEventListener('click', function () { show(at + 1); });
    stage.addEventListener('keydown', function (ev) {
      if (ev.key === 'ArrowRight' || ev.key === ' ' || ev.key === 'PageDown') { ev.preventDefault(); show(at + 1); }
      if (ev.key === 'ArrowLeft' || ev.key === 'PageUp') { ev.preventDefault(); show(at - 1); }
    });
    if (stage.requestFullscreen) {
      full.addEventListener('click', function () { stage.requestFullscreen(); stage.focus(); });
    } else { full.hidden = true; }
    document.addEventListener('fullscreenchange', fit);
    window.addEventListener('resize', fit);
    var m = location.hash.match(/^#slide-(\d+)$/);
    fit(); show(m ? parseInt(m[1], 10) - 1 : 0);
  });

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
