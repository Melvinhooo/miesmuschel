/* Magische Miesmuschel — Service Worker
 * Strategie: Cache-First fuer die App-Schale, Network-First fuer Daten-Dateien.
 * So hast du offline die letzte App-Version + die letzten Daten.
 */

const CACHE = 'miesmuschel-v1';
const SHELL = [
  './',
  './index.html',
  './assets/styles.css',
  './assets/app.js',
  './assets/icon.svg',
  './manifest.webmanifest'
];

self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(CACHE).then(c => c.addAll(SHELL)).then(() => self.skipWaiting())
  );
});

self.addEventListener('activate', event => {
  event.waitUntil(
    caches.keys()
      .then(keys => Promise.all(keys.filter(k => k !== CACHE).map(k => caches.delete(k))))
      .then(() => self.clients.claim())
  );
});

self.addEventListener('fetch', event => {
  const req = event.request;
  if (req.method !== 'GET') return;
  const url = new URL(req.url);

  // Daten-Dateien: Network-First (immer frische Tipps wenn online)
  if (url.pathname.includes('/data/')) {
    event.respondWith(
      fetch(req).then(res => {
        const clone = res.clone();
        caches.open(CACHE).then(c => c.put(req, clone));
        return res;
      }).catch(() => caches.match(req))
    );
    return;
  }

  // Alles andere: Cache-First
  event.respondWith(
    caches.match(req).then(cached => cached || fetch(req).then(res => {
      const clone = res.clone();
      caches.open(CACHE).then(c => c.put(req, clone));
      return res;
    }))
  );
});
