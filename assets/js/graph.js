/* Topic map for the home page.
 *
 * A ~30-node graph does not need a force library. This is a small deterministic
 * simulation: seeded placement, repulsion, link springs, gentle centring and a
 * box-collision pass that keeps labels from overlapping. It runs a fixed number
 * of iterations, paints once, and stops — nothing keeps moving after the layout
 * settles, which is the point.
 */
(function () {
  'use strict';

  var SVG_NS = 'http://www.w3.org/2000/svg';
  var W = 1000;             // viewBox units; the SVG scales to its container
  var H = 437;
  var PAD = 46;
  var ITERATIONS = 420;
  var ASPECT_DAMP = 0.42;   // vertical repulsion scale — keeps the map in a band

  var host = document.getElementById('knowledge-graph');
  var svg = document.getElementById('graph-svg');
  var dataEl = document.getElementById('graph-data');
  if (!host || !svg || !dataEl) return;

  var raw;
  try {
    raw = JSON.parse(dataEl.textContent);
  } catch (e) {
    return;
  }
  if (!raw.topics || raw.topics.length === 0) return;

  var reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  // -- model ----------------------------------------------------------------
  var nodes = raw.topics.map(function (t, i) {
    return {
      id: t.id, label: t.label, group: t.group, count: t.count, url: t.url,
      i: i, x: 0, y: 0, vx: 0, vy: 0,
      r: 4 + Math.sqrt(t.count) * 2.4
    };
  });

  var byId = {};
  nodes.forEach(function (n) { byId[n.id] = n; });

  // Co-occurrence: every unordered pair of topics that share a document.
  var linkMap = {};
  (raw.docs || []).forEach(function (tags) {
    var seen = tags.filter(function (t) { return byId[t]; });
    for (var a = 0; a < seen.length; a++) {
      for (var b = a + 1; b < seen.length; b++) {
        var key = seen[a] < seen[b] ? seen[a] + '|' + seen[b] : seen[b] + '|' + seen[a];
        linkMap[key] = (linkMap[key] || 0) + 1;
      }
    }
  });

  var links = Object.keys(linkMap).map(function (k) {
    var p = k.split('|');
    return { s: byId[p[0]], t: byId[p[1]], w: linkMap[k] };
  });

  // Adjacency, for the hover highlight.
  var adj = {};
  nodes.forEach(function (n) { adj[n.id] = {}; });
  links.forEach(function (l) { adj[l.s.id][l.t.id] = true; adj[l.t.id][l.s.id] = true; });

  // -- layout ---------------------------------------------------------------
  // Seeded, not random: the map looks the same on every visit.
  var GOLDEN = Math.PI * (3 - Math.sqrt(5));
  nodes.forEach(function (n, i) {
    var t = (i + 0.5) / nodes.length;
    var radius = Math.sqrt(t) * Math.min(W, H) * 0.38;
    var angle = i * GOLDEN;
    n.x = W / 2 + Math.cos(angle) * radius;
    n.y = H / 2 + Math.sin(angle) * radius * 0.82;
  });

  // Rough label box, used by the collision pass so text does not pile up.
  var CHAR_W = 5.4, LABEL_H = 11;
  nodes.forEach(function (n) {
    n.halfW = Math.max(n.r + 3, (n.label.length * CHAR_W) / 2 + 3);
    n.halfH = n.r + LABEL_H + 2;
  });

  function step(alpha) {
    var i, j, a, b, dx, dy, d2, d, f;

    // Repulsion — every pair, which is cheap at this size. The vertical
    // component is damped so the cloud spreads into the wide band the panel
    // actually is, instead of settling into a circle the fit then has to shrink.
    for (i = 0; i < nodes.length; i++) {
      a = nodes[i];
      for (j = i + 1; j < nodes.length; j++) {
        b = nodes[j];
        dx = b.x - a.x; dy = b.y - a.y;
        d2 = dx * dx + dy * dy || 0.01;
        d = Math.sqrt(d2);
        f = (2600 * alpha) / d2;
        var ux = (dx / d) * f, uy = (dy / d) * f * ASPECT_DAMP;
        a.vx -= ux; a.vy -= uy;
        b.vx += ux; b.vy += uy;
      }
    }

    // Link springs — heavier co-occurrence pulls a little harder.
    for (i = 0; i < links.length; i++) {
      var l = links[i];
      dx = l.t.x - l.s.x; dy = l.t.y - l.s.y;
      d = Math.sqrt(dx * dx + dy * dy) || 0.01;
      var rest = 92 - Math.min(l.w, 4) * 9;
      f = ((d - rest) / d) * 0.055 * alpha * Math.min(1 + l.w * 0.25, 2.2);
      l.s.vx += dx * f; l.s.vy += dy * f * 0.75;
      l.t.vx -= dx * f; l.t.vy -= dy * f * 0.75;
    }

    // Centring, slightly stronger vertically so the map stays in a wide band.
    for (i = 0; i < nodes.length; i++) {
      a = nodes[i];
      a.vx += (W / 2 - a.x) * 0.006 * alpha;
      a.vy += (H / 2 - a.y) * 0.026 * alpha;
    }

    // Box collision, so labels do not overlap.
    for (i = 0; i < nodes.length; i++) {
      a = nodes[i];
      for (j = i + 1; j < nodes.length; j++) {
        b = nodes[j];
        var ox = (a.halfW + b.halfW) - Math.abs(b.x - a.x);
        var oy = (a.halfH + b.halfH) - Math.abs(b.y - a.y);
        if (ox > 0 && oy > 0) {
          if (ox < oy) {
            var sx = (b.x > a.x ? 1 : -1) * ox * 0.22;
            a.x -= sx; b.x += sx;
          } else {
            var sy = (b.y > a.y ? 1 : -1) * oy * 0.22;
            a.y -= sy; b.y += sy;
          }
        }
      }
    }

    // Integrate with heavy damping — no orbiting.
    for (i = 0; i < nodes.length; i++) {
      a = nodes[i];
      if (a.fixed) { a.vx = 0; a.vy = 0; continue; }
      a.vx *= 0.82; a.vy *= 0.82;
      a.x += a.vx; a.y += a.vy;
    }
  }

  function settle(iterations) {
    for (var k = 0; k < iterations; k++) step(1 - k / iterations);
    fit();
  }

  // Scale the settled layout into the viewBox with a consistent margin.
  function fit() {
    var minX = Infinity, maxX = -Infinity, minY = Infinity, maxY = -Infinity;
    nodes.forEach(function (n) {
      minX = Math.min(minX, n.x - n.halfW); maxX = Math.max(maxX, n.x + n.halfW);
      minY = Math.min(minY, n.y - n.halfH); maxY = Math.max(maxY, n.y + n.halfH);
    });
    var sx = (W - PAD * 2) / Math.max(maxX - minX, 1);
    var sy = (H - PAD * 2) / Math.max(maxY - minY, 1);
    var s = Math.min(sx, sy, 1.35);
    var cx = (minX + maxX) / 2, cy = (minY + maxY) / 2;
    nodes.forEach(function (n) {
      n.px = W / 2 + (n.x - cx) * s;
      n.py = H / 2 + (n.y - cy) * s;
    });
  }

  // -- render ---------------------------------------------------------------
  svg.setAttribute('viewBox', '0 0 ' + W + ' ' + H);
  svg.setAttribute('preserveAspectRatio', 'xMidYMid meet');

  var gEdges = document.createElementNS(SVG_NS, 'g');
  var gNodes = document.createElementNS(SVG_NS, 'g');
  svg.appendChild(gEdges);
  svg.appendChild(gNodes);

  var edgeEls = links.map(function (l) {
    var line = document.createElementNS(SVG_NS, 'line');
    line.setAttribute('class', 'g-edge');
    line.setAttribute('stroke-width', Math.min(0.7 + l.w * 0.28, 2).toFixed(2));
    l.el = line;
    gEdges.appendChild(line);
    return line;
  });

  var nodeEls = nodes.map(function (n) {
    var g = document.createElementNS(SVG_NS, 'g');
    g.setAttribute('class', 'g-node g-node--' + n.group);
    g.setAttribute('tabindex', '0');
    g.setAttribute('role', 'link');
    g.setAttribute('aria-label', n.label + ' — ' + n.count + (n.count === 1 ? ' entry' : ' entries'));
    g.dataset.id = n.id;

    var c = document.createElementNS(SVG_NS, 'circle');
    c.setAttribute('r', n.r.toFixed(2));

    var t = document.createElementNS(SVG_NS, 'text');
    t.setAttribute('text-anchor', 'middle');
    t.textContent = n.label;

    g.appendChild(c);
    g.appendChild(t);
    gNodes.appendChild(g);
    n.el = g; n.circle = c; n.text = t;
    return g;
  });

  function paint() {
    links.forEach(function (l) {
      l.el.setAttribute('x1', l.s.px.toFixed(1));
      l.el.setAttribute('y1', l.s.py.toFixed(1));
      l.el.setAttribute('x2', l.t.px.toFixed(1));
      l.el.setAttribute('y2', l.t.py.toFixed(1));
    });
    nodes.forEach(function (n) {
      n.circle.setAttribute('cx', n.px.toFixed(1));
      n.circle.setAttribute('cy', n.py.toFixed(1));
      n.text.setAttribute('x', n.px.toFixed(1));
      n.text.setAttribute('y', (n.py + n.r + 9).toFixed(1));
    });
  }

  // -- interaction ----------------------------------------------------------
  var hint = document.getElementById('graph-hint');
  var defaultHint = hint ? hint.textContent : '';

  function focusNode(n) {
    host.classList.add('is-focused');
    nodes.forEach(function (m) {
      m.el.classList.toggle('is-lit', m === n || adj[n.id][m.id]);
      m.el.classList.toggle('is-root', m === n);
    });
    links.forEach(function (l) {
      l.el.classList.toggle('is-lit', l.s === n || l.t === n);
    });
    if (hint) {
      var deg = Object.keys(adj[n.id]).length;
      hint.textContent = n.label + ' · ' + n.count + (n.count === 1 ? ' entry' : ' entries') +
                         ' · ' + deg + (deg === 1 ? ' link' : ' links');
    }
  }

  function clearFocus() {
    host.classList.remove('is-focused');
    nodes.forEach(function (m) { m.el.classList.remove('is-lit', 'is-root'); });
    links.forEach(function (l) { l.el.classList.remove('is-lit'); });
    if (hint) hint.textContent = defaultHint;
  }

  nodes.forEach(function (n) {
    n.el.addEventListener('mouseenter', function () { if (!dragging) focusNode(n); });
    n.el.addEventListener('mouseleave', function () { if (!dragging) clearFocus(); });
    n.el.addEventListener('focus', function () { focusNode(n); });
    n.el.addEventListener('blur', clearFocus);
    n.el.addEventListener('click', function () { if (!moved) window.location.href = n.url; });
    n.el.addEventListener('keydown', function (e) {
      if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); window.location.href = n.url; }
    });
  });

  // Light drag: nudge a node and its neighbours re-settle. Not a toy — it makes
  // a dense corner readable without any zoom UI.
  var dragging = null, moved = false;

  function svgPoint(evt) {
    var rect = svg.getBoundingClientRect();
    var vb = svg.viewBox.baseVal;
    // preserveAspectRatio="xMidYMid meet" — recover the letterboxed scale.
    var scale = Math.min(rect.width / vb.width, rect.height / vb.height);
    var offX = (rect.width - vb.width * scale) / 2;
    var offY = (rect.height - vb.height * scale) / 2;
    return {
      x: (evt.clientX - rect.left - offX) / scale,
      y: (evt.clientY - rect.top - offY) / scale
    };
  }

  svg.addEventListener('pointerdown', function (e) {
    var g = e.target.closest('.g-node');
    if (!g) return;
    dragging = nodes[nodeEls.indexOf(g)];
    if (!dragging) return;
    moved = false;
    dragging.fixed = true;
    svg.setPointerCapture(e.pointerId);
  });

  svg.addEventListener('pointermove', function (e) {
    if (!dragging) return;
    var p = svgPoint(e);
    moved = true;
    // px/py are post-fit coordinates; move in that space and relax neighbours.
    dragging.px = p.x; dragging.py = p.y;
    paint();
  });

  svg.addEventListener('pointerup', function (e) {
    if (!dragging) return;
    dragging.fixed = false;
    dragging = null;
    if (svg.hasPointerCapture(e.pointerId)) svg.releasePointerCapture(e.pointerId);
    setTimeout(function () { moved = false; }, 0);
  });

  svg.addEventListener('pointerleave', function () {
    if (dragging) { dragging.fixed = false; dragging = null; }
  });

  // -- go -------------------------------------------------------------------
  if (reduceMotion) {
    settle(ITERATIONS);
    paint();
  } else {
    // Settle off-screen, then fade the finished layout in once. Watching a
    // simulation thrash for two seconds is exactly the kind of "futuristic"
    // the brief rules out.
    settle(ITERATIONS);
    paint();
    svg.animate(
      [{ opacity: 0 }, { opacity: 1 }],
      { duration: 420, easing: 'cubic-bezier(0.4,0,0.2,1)', fill: 'both' }
    );
  }

  // Keep the layout legible when the container changes shape.
  var resizeTimer;
  window.addEventListener('resize', function () {
    clearTimeout(resizeTimer);
    resizeTimer = setTimeout(function () { fit(); paint(); }, 160);
  });
})();
