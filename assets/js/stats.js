/* Visit and download counts in the post byline.
 *
 * The site is static, so the numbers come from GoatCounter's public per-path
 * counter endpoint — readable without an API key once "allow public statistics"
 * is enabled on the site.
 *
 * Everything here fails silently: if the endpoint is unreachable, blocked by an
 * extension, or has no hits for a path yet, the byline simply shows nothing
 * rather than a misleading zero.
 */
(function () {
  'use strict';

  var host = document.getElementById('post-stats');
  if (!host) return;

  var code = host.dataset.gc;
  if (!code) return;

  var base = 'https://' + code + '.goatcounter.com';

  // -- reading --------------------------------------------------------------

  // GoatCounter normalises trailing slashes inconsistently between the recorded
  // path and the counter lookup, so try the path as-is and then trimmed.
  function variants(path) {
    var out = [path];
    if (path.length > 1 && path.charAt(path.length - 1) === '/') {
      out.push(path.slice(0, -1));
    } else {
      out.push(path + '/');
    }
    return out;
  }

  function fetchCount(path) {
    var tries = variants(path);

    function attempt(i) {
      if (i >= tries.length) return Promise.resolve(null);
      var url = base + '/counter' + tries[i] + '.json';
      return fetch(url, { mode: 'cors', credentials: 'omit' })
        .then(function (r) { return r.ok ? r.json() : null; })
        .then(function (d) {
          if (d && d.count != null) return d.count;
          return attempt(i + 1);
        })
        .catch(function () { return attempt(i + 1); });
    }

    return attempt(0);
  }

  // The endpoint returns a pre-formatted string ("1,234"); keep digits only so
  // the page can apply its own locale formatting.
  function toNumber(v) {
    if (v == null) return null;
    var n = parseInt(String(v).replace(/[^\d]/g, ''), 10);
    return isFinite(n) ? n : null;
  }

  function render(el, n, one, many) {
    if (n == null || n <= 0) return false;
    el.textContent = n.toLocaleString() + ' ' + (n === 1 ? one : many);
    el.hidden = false;
    return true;
  }

  var visitsEl = host.querySelector('[data-stat="visits"]');
  var dlEl = host.querySelector('[data-stat="downloads"]');
  var docId = host.dataset.docId || '';

  var jobs = [
    fetchCount(host.dataset.path || location.pathname).then(function (c) {
      return render(visitsEl, toNumber(c), 'visit', 'visits');
    })
  ];

  if (dlEl && docId) {
    jobs.push(
      fetchCount('/download/' + docId).then(function (c) {
        return render(dlEl, toNumber(c), 'download', 'downloads');
      })
    );
  }

  Promise.all(jobs).then(function (shown) {
    // Only reveal the separator once at least one number actually arrived.
    if (shown.indexOf(true) !== -1) host.hidden = false;
  });

  // -- counting a download --------------------------------------------------

  document.addEventListener('click', function (e) {
    var a = e.target.closest('[data-download]');
    if (!a) return;
    if (!window.goatcounter || typeof window.goatcounter.count !== 'function') return;

    window.goatcounter.count({
      path: '/download/' + a.dataset.download,
      title: a.dataset.downloadTitle || document.title,
      event: true
    });
  });
})();
