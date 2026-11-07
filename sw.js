// NecroCounter service worker
const VERSION = "necrocounter-0.2.3";
const CORE = ["./", "./index.html", "./manifest.webmanifest", "./icon-192.png", "./icon-512.png", "./icon-maskable-512.png", "./apple-touch-icon.png", "./favicon-32.png",
  "./data/n23/index.json",
  "./data/n23/maisons/cawdor.json", "./data/n23/maisons/delaque.json", "./data/n23/maisons/escher.json",
  "./data/n23/maisons/goliath.json", "./data/n23/maisons/orlock.json", "./data/n23/maisons/van-saar.json"
];

self.addEventListener("install", e => {
  e.waitUntil(caches.open(VERSION).then(c => c.addAll(CORE.map(u => new Request(u, { cache: "reload" })))).then(() => self.skipWaiting()));
});

self.addEventListener("activate", e => {
  e.waitUntil(caches.keys().then(keys => Promise.all(keys.filter(k => k !== VERSION).map(k => caches.delete(k)))).then(() => self.clients.claim()));
});

self.addEventListener("fetch", e => {
  const req = e.request;
  if (req.method !== "GET") return;
  e.respondWith(
    fetch(req).then(res => {
      const copy = res.clone();
      caches.open(VERSION).then(c => c.put(req, copy)).catch(() => {});
      return res;
    }).catch(() => caches.open(VERSION).then(c => c.match(req).then(hit => hit || c.match("./index.html"))))
  );
});
