---
permalink: /sw.js
sitemap: false
---
/* Tombstone for the service worker the previous theme registered.
 *
 * Returning visitors still have that worker installed and would otherwise be
 * served the old cached site indefinitely. This replaces it, drops every cache
 * it created, and unregisters itself so the next load is a normal one.
 */
self.addEventListener('install', function (event) {
  self.skipWaiting();
});

self.addEventListener('activate', function (event) {
  event.waitUntil(
    caches.keys()
      .then(function (keys) { return Promise.all(keys.map(function (k) { return caches.delete(k); })); })
      .then(function () { return self.registration.unregister(); })
      .then(function () { return self.clients.matchAll({ type: 'window' }); })
      .then(function (clients) { clients.forEach(function (c) { c.navigate(c.url); }); })
  );
});
