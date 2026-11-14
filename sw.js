// NecroCounter service worker
const VERSION = "necrocounter-1.11.1";
const CORE = ["./", "./index.html", "./manifest.webmanifest", "./icon-192.png", "./icon-512.png", "./icon-maskable-512.png", "./apple-touch-icon.png", "./favicon-32.png", "./compte.js",
  "./data/n23/armes.json", "./data/n23/comptoir.json", "./data/n23/index.json", "./data/n23/maisons/cawdor.json", "./data/n23/maisons/delaque.json", "./data/n23/maisons/escher.json", "./data/n23/maisons/goliath.json", "./data/n23/maisons/orlock.json", "./data/n23/maisons/van-saar.json", "./data/n23/maisons/squats.json", "./data/n23/maisons/nomades.json", "./data/n23/maisons/venators.json", "./data/n23/maisons/enforcers.json", "./data/n23/maisons/corpse-grinder.json", "./data/n23/maisons/culte-chaos.json", "./data/n23/maisons/culte-genestealer.json", "./data/n23/maisons/proscrits.json", "./data/n23/maisons/spyriens.json", "./data/n23/maisons/orlock-fer.json", "./data/n23/mercenaires.json", "./data/n23/refs.json", "./data/n23/campagne.json", "./data/n23/scenarios.json"];

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
    // Same origin : on revalide toujours auprès du serveur (pas de copie périmée du cache HTTP)
    fetch(req, new URL(req.url).origin === location.origin ? { cache: "no-cache" } : {}).then(res => {
      const copy = res.clone();
      caches.open(VERSION).then(c => c.put(req, copy)).catch(() => {});
      return res;
    }).catch(() => caches.open(VERSION).then(c => c.match(req).then(hit => hit || (req.mode === "navigate" ? c.match("./index.html") : Response.error()))))
  );
});
