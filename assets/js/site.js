/* Site chrome: theme, navigation, addresses, table of contents, filters. */
(function () {
  'use strict';

  var root = document.documentElement;

  // -- theme ----------------------------------------------------------------
  function syncThemeIcon() {
    var dark = root.getAttribute('data-theme') === 'dark';
    var sun = document.querySelector('[data-icon="sun"]');
    var moon = document.querySelector('[data-icon="moon"]');
    if (sun) sun.hidden = dark;
    if (moon) moon.hidden = !dark;
  }

  var toggle = document.getElementById('theme-toggle');
  if (toggle) {
    syncThemeIcon();
    toggle.addEventListener('click', function () {
      var next = root.getAttribute('data-theme') === 'dark' ? 'light' : 'dark';
      root.setAttribute('data-theme', next);
      try { localStorage.setItem('theme', next); } catch (e) { /* private mode */ }
      syncThemeIcon();
    });
  }

  // Follow the OS only while the visitor has not chosen for themselves.
  var mq = window.matchMedia('(prefers-color-scheme: dark)');
  var onScheme = function (e) {
    var chosen = null;
    try { chosen = localStorage.getItem('theme'); } catch (err) { /* ignore */ }
    if (chosen) return;
    root.setAttribute('data-theme', e.matches ? 'dark' : 'light');
    syncThemeIcon();
  };
  if (mq.addEventListener) mq.addEventListener('change', onScheme);

  // -- mobile navigation ----------------------------------------------------
  var navBtn = document.querySelector('.navtoggle');
  var nav = document.getElementById('primary-nav');

  function isCompact() { return window.matchMedia('(max-width: 47.99em)').matches; }

  function setNav(open) {
    if (!nav || !navBtn) return;
    nav.hidden = !open;
    navBtn.setAttribute('aria-expanded', String(open));
  }

  if (navBtn && nav) {
    if (isCompact()) setNav(false);
    navBtn.addEventListener('click', function () {
      setNav(nav.hidden);
    });
    document.addEventListener('keydown', function (e) {
      if (e.key === 'Escape' && isCompact() && !nav.hidden) { setNav(false); navBtn.focus(); }
    });
    window.addEventListener('resize', function () {
      if (!isCompact()) { nav.hidden = false; navBtn.setAttribute('aria-expanded', 'false'); }
      else if (navBtn.getAttribute('aria-expanded') !== 'true') { nav.hidden = true; }
    });
  }

  // -- email addresses ------------------------------------------------------
  // Assembled here rather than sitting in the HTML as a harvestable mailto.
  Array.prototype.forEach.call(
    document.querySelectorAll('[data-mail-user][data-mail-domain]'),
    function (a) {
      var addr = a.dataset.mailUser + '@' + a.dataset.mailDomain;
      a.setAttribute('href', 'mailto:' + addr);
      if (a.dataset.mailShow === 'true') a.textContent = addr;
    }
  );

  // -- wide tables ----------------------------------------------------------
  Array.prototype.forEach.call(document.querySelectorAll('.prose table'), function (t) {
    if (t.parentElement && t.parentElement.classList.contains('table-wrap')) return;
    var wrap = document.createElement('div');
    wrap.className = 'table-wrap';
    t.parentNode.insertBefore(wrap, t);
    wrap.appendChild(t);
  });

  // -- table of contents ----------------------------------------------------
  // Built from the rendered document rather than from Liquid: kramdown already
  // assigns the heading ids, and this keeps the templates free of parsing.
  var toc = document.querySelector('.toc');
  if (toc) {
    var headings = Array.prototype.slice.call(
      document.querySelectorAll('.prose h2[id], .prose h3[id]')
    );
    var linkFor = {};

    if (headings.length >= 2) {
      var ul = toc.querySelector('ul');
      headings.forEach(function (h) {
        var li = document.createElement('li');
        if (h.tagName === 'H3') li.className = 'toc__l3';
        var a = document.createElement('a');
        a.href = '#' + h.id;
        a.textContent = h.textContent.replace(/¶\s*$/, '').trim();
        li.appendChild(a);
        ul.appendChild(li);
        linkFor[h.id] = a;
      });
      toc.hidden = false;
    }

    if (headings.length >= 2 && 'IntersectionObserver' in window) {
      var visible = new Set();
      var observer = new IntersectionObserver(function (entries) {
        entries.forEach(function (en) {
          if (en.isIntersecting) visible.add(en.target.id);
          else visible.delete(en.target.id);
        });
        var current = headings.filter(function (h) { return visible.has(h.id); })[0];
        if (!current) return;
        Object.keys(linkFor).forEach(function (id) {
          linkFor[id].classList.toggle('is-active', id === current.id);
        });
      }, { rootMargin: '-72px 0px -70% 0px', threshold: 0 });
      headings.forEach(function (h) { observer.observe(h); });
    }
  }

  // -- notes filter ---------------------------------------------------------
  var bar = document.querySelector('.filterbar');
  var list = document.getElementById('entry-list');
  if (bar && list) {
    var empty = document.getElementById('filter-empty');
    var counter = document.getElementById('filter-count');

    bar.addEventListener('click', function (e) {
      var btn = e.target.closest('.filterbtn');
      if (!btn) return;

      Array.prototype.forEach.call(bar.querySelectorAll('.filterbtn'), function (b) {
        b.setAttribute('aria-pressed', String(b === btn));
      });

      var key = btn.dataset.filterKey || '';
      var value = btn.dataset.filterValue || '';
      var shown = 0;

      Array.prototype.forEach.call(list.children, function (li) {
        var match = !value;
        if (value) {
          var field = li.dataset[key] || '';
          match = key === 'topics'
            ? (' ' + field + ' ').indexOf(' ' + value + ' ') !== -1
            : field === value;
        }
        li.hidden = !match;
        if (match) shown++;
      });

      if (empty) empty.hidden = shown !== 0;
      if (counter) counter.textContent = shown + (shown === 1 ? ' entry' : ' entries');
    });
  }
})();
