// frontend/sw.js
const CACHE = 'mpesa-toolkit-v1';
const urls = [
  '/',
  '/index.html',
  '/dashboard.html',
  '/register.html',
  '/login.html',
  '/manifest.json',
  '/js/api.js',
  '/js/auth.js',
  '/js/qr-generator.js'
];
self.addEventListener('install', e => e.waitUntil(caches.open(CACHE).then(c => c.addAll(urls))));
self.addEventListener('fetch', e => e.respondWith(caches.match(e.request).then(r => r || fetch(e.request))));