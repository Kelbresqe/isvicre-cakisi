// İsviçre Çakısı - Service Worker v1.0.0
const CACHE_NAME = 'isvicre-cakisi-v1';
const OFFLINE_URL = '/offline';

// Statik dosyalar - her zaman önbelleğe al
const STATIC_ASSETS = [
  '/',
  '/static/manifest.json',
  '/static/images/icon-192.svg',
  '/static/images/icon-512.svg'
];

// Install event - statik dosyaları önbelleğe al
self.addEventListener('install', (event) => {
  console.log('[SW] Install');
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      console.log('[SW] Caching static assets');
      return cache.addAll(STATIC_ASSETS);
    })
  );
  // Hemen aktifleştir
  self.skipWaiting();
});

// Activate event - eski cache'leri temizle
self.addEventListener('activate', (event) => {
  console.log('[SW] Activate');
  event.waitUntil(
    caches.keys().then((cacheNames) => {
      return Promise.all(
        cacheNames
          .filter((name) => name !== CACHE_NAME)
          .map((name) => {
            console.log('[SW] Deleting old cache:', name);
            return caches.delete(name);
          })
      );
    })
  );
  // Tüm sayfalar için hemen kontrolü al
  self.clients.claim();
});

// Fetch event - Network First stratejisi (araçlar dinamik olduğu için)
self.addEventListener('fetch', (event) => {
  const { request } = event;
  const url = new URL(request.url);

  // Sadece GET requestlerini ele al
  if (request.method !== 'GET') return;

  // API ve form isteklerini atla
  if (url.pathname.startsWith('/api/') || 
      url.pathname.startsWith('/tools/') && request.headers.get('HX-Request')) {
    return;
  }

  // Statik dosyalar için Cache First
  if (url.pathname.startsWith('/static/')) {
    event.respondWith(
      caches.match(request).then((cachedResponse) => {
        if (cachedResponse) {
          return cachedResponse;
        }
        return fetch(request).then((response) => {
          // Sadece başarılı yanıtları önbelleğe al
          if (response.ok) {
            const responseClone = response.clone();
            caches.open(CACHE_NAME).then((cache) => {
              cache.put(request, responseClone);
            });
          }
          return response;
        });
      })
    );
    return;
  }

  // Sayfa istekleri için Network First, fallback to cache
  event.respondWith(
    fetch(request)
      .then((response) => {
        // Başarılı yanıtları önbelleğe al
        if (response.ok && url.origin === location.origin) {
          const responseClone = response.clone();
          caches.open(CACHE_NAME).then((cache) => {
            cache.put(request, responseClone);
          });
        }
        return response;
      })
      .catch(() => {
        // Offline - önbellekten dene
        return caches.match(request).then((cachedResponse) => {
          if (cachedResponse) {
            return cachedResponse;
          }
          // Ana sayfa için fallback
          if (url.pathname === '/' || url.pathname === '') {
            return caches.match('/');
          }
          // Offline sayfası göster
          return new Response(
            `<!DOCTYPE html>
            <html lang="tr">
            <head>
              <meta charset="UTF-8">
              <meta name="viewport" content="width=device-width, initial-scale=1.0">
              <title>Çevrimdışı - İsviçre Çakısı</title>
              <style>
                body { font-family: system-ui, sans-serif; background: #0f172a; color: #fff; display: flex; align-items: center; justify-content: center; min-height: 100vh; margin: 0; text-align: center; }
                .container { max-width: 400px; padding: 2rem; }
                h1 { font-size: 4rem; margin: 0; }
                p { color: #94a3b8; font-size: 1.125rem; }
                button { background: #10b981; color: #fff; border: none; padding: 0.75rem 1.5rem; border-radius: 0.5rem; font-size: 1rem; cursor: pointer; margin-top: 1rem; }
                button:hover { background: #059669; }
              </style>
            </head>
            <body>
              <div class="container">
                <h1>📡</h1>
                <h2>Çevrimdışısınız</h2>
                <p>İnternet bağlantınız yok gibi görünüyor. Bağlantınızı kontrol edip tekrar deneyin.</p>
                <button onclick="location.reload()">Tekrar Dene</button>
              </div>
            </body>
            </html>`,
            { headers: { 'Content-Type': 'text/html; charset=utf-8' } }
          );
        });
      })
  );
});

// Background Sync - gelecekte form istekleri için
self.addEventListener('sync', (event) => {
  console.log('[SW] Background Sync:', event.tag);
});

// Push Notifications - gelecek için hazır
self.addEventListener('push', (event) => {
  console.log('[SW] Push received');
  const options = {
    body: event.data?.text() || 'Yeni bir güncelleme var!',
    icon: '/static/images/icon-192.png',
    badge: '/static/images/icon-192.png',
    vibrate: [100, 50, 100],
    data: { dateOfArrival: Date.now() }
  };
  event.waitUntil(
    self.registration.showNotification('İsviçre Çakısı', options)
  );
});
