const CACHE_NAME = 'team-dashboard-cache-v1';
const urlsToCache = [
  'team_dashboard.html',
  'manifest.json',
  'https://cdnjs.cloudflare.com/ajax/libs/paho-mqtt/1.0.1/mqttws31.min.js'
  // Add any other assets (CSS, images, etc.) as needed.
];

self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then(cache => {
        console.log('Opened cache');
        return cache.addAll(urlsToCache);
      })
  );
});

self.addEventListener('fetch', event => {
  event.respondWith(
    caches.match(event.request)
      .then(response => {
        // Return cached response if available; otherwise fetch from network.
        return response || fetch(event.request);
      })
  );
});
