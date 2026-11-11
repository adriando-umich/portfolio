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

  // Projects page: filter by industry, task and tool
  var filter = document.querySelector('.filter');
  if (!filter) return;
  var NAMES = {};
  Array.prototype.forEach.call(document.querySelectorAll('[data-f]'), function (b) { NAMES[b.getAttribute('data-f') + ':' + b.getAttribute('data-v')] = b.textContent.trim(); });
  var state = { type: '', industry: '', task: '', tool: '' };
  var items = Array.prototype.slice.call(document.querySelectorAll('[data-tools]'));
  var groups = Array.prototype.slice.call(document.querySelectorAll('.group'));
  var empty = document.querySelector('.empty'), clear = filter.querySelector('.clear'), active = filter.querySelector('.active');
  function has(list, v) { return (' ' + list + ' ').indexOf(' ' + v + ' ') > -1; }
  function apply() {
    var shown = 0;
    items.forEach(function (el) {
      var on = (!state.type || el.getAttribute('data-type') === state.type) && (!state.industry || el.getAttribute('data-industry') === state.industry) &&
        (!state.task || has(el.getAttribute('data-tasks'), state.task)) &&
        (!state.tool || has(el.getAttribute('data-tools'), state.tool));
      el.hidden = !on;
      if (on) shown += 1;
    });
    groups.forEach(function (g) { g.hidden = !g.querySelector('[data-tools]:not([hidden])'); });
    empty.style.display = shown ? 'none' : 'block';
    Array.prototype.forEach.call(document.querySelectorAll('[data-f]'), function (b) {
      b.setAttribute('aria-pressed', String(state[b.getAttribute('data-f')] === b.getAttribute('data-v')));
    });
    Array.prototype.forEach.call(document.querySelectorAll('.matrix .cell'), function (b) {
      b.setAttribute('aria-pressed', String(state.industry === b.getAttribute('data-i') && state.task === b.getAttribute('data-t')));
    });
    var parts = [];
    ['type', 'task', 'industry', 'tool'].forEach(function (k) { if (state[k]) parts.push(NAMES[k + ':' + state[k]]); });
    active.textContent = parts.length ? shown + ' shown: ' + parts.join(', ') : '';
    clear.hidden = !parts.length;
  }
  document.addEventListener('click', function (ev) {
    var b = ev.target.closest ? ev.target.closest('[data-f], .matrix .cell, .filter .clear') : null;
    if (!b) return;
    if (b.classList.contains('clear')) { state = { type: '', industry: '', task: '', tool: '' }; }
    else if (b.classList.contains('cell')) {
      var same = state.industry === b.getAttribute('data-i') && state.task === b.getAttribute('data-t');
      state.industry = same ? '' : b.getAttribute('data-i');
      state.task = same ? '' : b.getAttribute('data-t');
    } else {
      var k = b.getAttribute('data-f'), v = b.getAttribute('data-v');
      state[k] = state[k] === v ? '' : v;
    }
    apply();
  });
  (location.hash.slice(1).split('&')).forEach(function (kv) {
    var p = kv.split('=');
    if (state.hasOwnProperty(p[0]) && /^[a-z]+$/.test(p[1] || '')) state[p[0]] = p[1];
  });
  apply();
})();
