/* Magische Miesmuschel — Service Worker
 * Strategie: Cache-First fuer die App-Schale, Network-First fuer Daten-Dateien.
 * So hast du offline die letzte App-Version + die letzten Daten.
 */

const CACHE = 'miesmuschel-v6';
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

// Web Push: Notification anzeigen wenn ein Push reinkommt
self.addEventListener('push', event => {
  let data = { title: '🐚 Magische Miesmuschel', body: 'Update verfuegbar', url: '/' };
  if (event.data) {
    try { data = Object.assign(data, event.data.json()); }
    catch (e) { data.body = event.data.text(); }
  }
  event.waitUntil(
    self.registration.showNotification(data.title, {
      body: data.body,
      icon: 'assets/icon.svg',
      badge: 'assets/icon.svg',
      tag: data.tag || 'miesmuschel',
      data: { url: data.url || '/' }
    })
  );
});

// Klick auf die Notification: PWA oeffnen / fokussieren
self.addEventListener('notificationclick', event => {
  event.notification.close();
  const targetUrl = (event.notification.data && event.notification.data.url) || '/';
  event.waitUntil(
    clients.matchAll({ type: 'window', includeUncontrolled: true }).then(list => {
      for (const c of list) {
        if (c.url.includes(targetUrl) && 'focus' in c) return c.focus();
      }
      if (clients.openWindow) return clients.openWindow(targetUrl);
    })
  );
});
