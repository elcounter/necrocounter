// ---------- NecroCounter : compte (Supabase), synchronisation, profil joueur et carte communautaire ----------
// Même projet Supabase que WarCounter et SpearCounter : un seul compte pour les trois apps, profils et carte partagés.
// Données synchronisées : toutes les clés localStorage « nc_* » (gangs, partie en cours, historique), table necro_data.
(function(){
  const SB = "https://agqdwjkxeodxdrujphrv.supabase.co", SBK = "sb_publishable_B0a1M8wjrilqmHfGnAErMQ_iueIp0g8";
  const PFX = "nc_", SK = {sess:"necrocounter-session", meta:"necrocounter-sync"};
  const SKIP = new Set([SK.sess, SK.meta]);
  const $ = id => document.getElementById(id);
  const esc = s => String(s == null ? "" : s).replace(/[&<>"']/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
  const ls = {get:k => { try { return JSON.parse(localStorage.getItem(k)); } catch(e) { return null; } },
    set:(k, v) => { try { RAW_SET.call(localStorage, k, JSON.stringify(v)); } catch(e) {} }, del:k => { try { RAW_DEL.call(localStorage, k); } catch(e) {} }};
  const RAW_SET = Storage.prototype.setItem, RAW_DEL = Storage.prototype.removeItem;
  const synced = k => typeof k === "string" && k.startsWith(PFX) && !SKIP.has(k);
  // Toute écriture de l'app (gangs, partie, historique) marque les données à envoyer
  Storage.prototype.setItem = function(k, v){ RAW_SET.call(this, k, v); if (this === localStorage && synced(k)) dirty(); };
  Storage.prototype.removeItem = function(k){ RAW_DEL.call(this, k); if (this === localStorage && synced(k)) dirty(); };

  let sess = ls.get(SK.sess), accMsg = "", accErr = false, accBusy = false, delArmed = false, pushT = null;
  async function api(path, opt = {}, auth = true){
    const h = Object.assign({apikey:SBK, "Content-Type":"application/json"}, opt.headers || {});
    if (auth && sess) h.Authorization = "Bearer " + sess.access_token;
    const r = await fetch(SB + path, Object.assign({}, opt, {headers:h}));
    const t = await r.text(); let j = null; try { j = t ? JSON.parse(t) : null; } catch(e) {}
    if (!r.ok) { const e = new Error((j && (j.msg || j.message || j.error_description || j.error)) || "Erreur " + r.status); e.status = r.status; throw e; }
    return j;
  }
  function setSess(j){
    sess = {access_token:j.access_token, refresh_token:j.refresh_token, expires_at:Date.now() / 1000 + (j.expires_in || 3600),
      email:(j.user || {}).email || (sess || {}).email, uid:(j.user || {}).id || (sess || {}).uid};
    ls.set(SK.sess, sess);
  }
  function clearSess(){ sess = null; ls.del(SK.sess); ls.del(SK.meta); }
  async function fresh(){
    if (!sess) return false;
    if (sess.expires_at - 60 > Date.now() / 1000) return true;
    try { setSess(await api("/auth/v1/token?grant_type=refresh_token", {method:"POST", body:JSON.stringify({refresh_token:sess.refresh_token})}, false)); return true; }
    catch(e) { if (e.status === 400 || e.status === 401) clearSess(); return false; }   // hors ligne : on garde la session
  }
  const frMsg = m => /invalid login/i.test(m) ? "E-mail ou mot de passe incorrect." : /already registered|already exists/i.test(m) ? "Un compte existe déjà avec cet e-mail : connecte-toi." : /password.*(6|characters)/i.test(m) ? "Le mot de passe doit faire au moins 6 caractères." : /valid email|invalid.*email/i.test(m) ? "Adresse e-mail invalide." : /fetch|network/i.test(m) ? "Connexion impossible : vérifie ton accès à Internet." : /necro_data|relation|schema cache/i.test(m) ? "Le serveur n'est pas encore prêt pour NecroCounter." : m;

  // ---------- Synchronisation : toutes les clés nc_* de l'appareil ----------
  function localData(){
    const d = {};
    for (let i = 0; i < localStorage.length; i++) { const k = localStorage.key(i); if (synced(k)) { try { d[k] = JSON.parse(localStorage.getItem(k)); } catch(e) {} } }
    return d;
  }
  function writeLocal(d){
    Object.keys(localData()).forEach(k => { if (!(k in d)) RAW_DEL.call(localStorage, k); });
    Object.entries(d || {}).forEach(([k, v]) => { if (synced(k)) RAW_SET.call(localStorage, k, JSON.stringify(v)); });
  }
  async function pull(){ const r = await api(`/rest/v1/necro_data?select=data,updated_at&user_id=eq.${sess.uid}`); return (r || [])[0] || null; }
  async function push(){
    const at = new Date().toISOString();
    await api("/rest/v1/necro_data", {method:"POST", headers:{Prefer:"resolution=merge-duplicates,return=minimal"},
      body:JSON.stringify({user_id:sess.uid, data:localData(), updated_at:at})});
    ls.set(SK.meta, {at, dirty:false});
  }
  function mergeRemote(R){   // première connexion sur cet appareil : on additionne local et compte
    const L = localData(), RD = (R && R.data) || {}, out = Object.assign({}, RD, L);
    ["nc_gangs_v1", "nc_match_history_v1"].forEach(k => {
      const a = Array.isArray(RD[k]) ? RD[k] : [], b = Array.isArray(L[k]) ? L[k] : [];
      const key = x => (x && x.id) || JSON.stringify(x), seen = new Set(b.map(key));
      out[k] = b.concat(a.filter(x => !seen.has(key(x))));
    });
    writeLocal(out);
  }
  async function sync(first){
    if (!(await fresh())) return;
    try {
      const m = ls.get(SK.meta) || {}, r = await pull();
      if (first) { if (r) mergeRemote(r); await push(); location.reload(); return; }
      if (r && !m.dirty && (!m.at || Date.parse(r.updated_at) > Date.parse(m.at))) {
        writeLocal(r.data || {}); ls.set(SK.meta, {at:r.updated_at, dirty:false}); location.reload(); return;
      }
      if (m.dirty || !r) await push();
    } catch(e) { accMsg = "Synchronisation impossible : " + frMsg(e.message); accErr = true; if (location.hash === "#compte") renderAccount(); }
  }
  function dirty(){
    if (!sess) return;
    ls.set(SK.meta, Object.assign(ls.get(SK.meta) || {}, {dirty:true}));
    clearTimeout(pushT); pushT = setTimeout(() => { fresh().then(ok => ok && push()).catch(() => {}); }, 2000);
  }
  if (sess) sync(false);
  document.addEventListener("visibilitychange", () => { if (document.visibilityState === "visible" && sess) sync(false); });
  window.addEventListener("online", () => { if (sess) sync(false); });

  // ---------- Profil joueur (carte communautaire, partagé avec WarCounter et SpearCounter) ----------
  const FACS = () => ["Maison Cawdor", "Maison Delaque", "Maison Escher", "Maison Goliath", "Maison Orlock", "Maison Van Saar", "Prospecteurs Squats Ironhead", "Nomades des Désolations"];
  let prof = null, profLoaded = false, profCity = null, cityT = null, profClub = null, clubT = null;
  const likeQ = q => q.replace(/[%_*,()\\]/g, " ").trim();
  async function clubSuggest(q){
    const box = $("pf-csug"); if (!box) return;
    if (q.length < 2) { box.hidden = true; return; }
    try {
      const L = await api(`/rest/v1/clubs?select=id,name&name=ilike.*${encodeURIComponent(likeQ(q))}*&order=name&limit=6`);
      const exact = L.some(c => c.name.toLowerCase() === q.toLowerCase());
      box.innerHTML = L.map(c => `<button type="button" data-club="${esc(JSON.stringify(c))}">Rejoindre <b>${esc(c.name)}</b></button>`).join("")
        + (exact ? "" : `<p class="hint pf-new">${L.length ? "Sinon, le club" : "Nouveau club :"} « ${esc(q)} » sera créé à l'enregistrement.</p>`);
      box.hidden = false;
    } catch(e) { box.hidden = true; }
  }
  async function resolveClub(name){   // club choisi, existant (même nom) ou créé
    if (!name) return null;
    if (profClub && profClub.name.toLowerCase() === name.toLowerCase()) return profClub;
    const f = await api(`/rest/v1/clubs?select=id,name&name=ilike.${encodeURIComponent(likeQ(name))}&limit=1`);
    if (f.length) return f[0];
    try { const c = await api("/rest/v1/clubs", {method:"POST", headers:{Prefer:"return=representation"}, body:JSON.stringify({name, created_by:sess.uid})}); return c[0]; }
    catch(e) { const g = await api(`/rest/v1/clubs?select=id,name&name=ilike.${encodeURIComponent(likeQ(name))}&limit=1`); if (g.length) return g[0]; throw e; }
  }
  async function loadProfile(){
    try { if (await fresh()) { const r = await api(`/rest/v1/profiles?select=*&user_id=eq.${sess.uid}`); prof = (r || [])[0] || null; profCity = prof && prof.city ? {city:prof.city, insee:prof.insee, lat:prof.lat, lng:prof.lng} : null; profClub = prof && prof.club_id ? {id:prof.club_id, name:prof.club} : null; } }
    catch(e) { accMsg = "Profil indisponible : " + frMsg(e.message); accErr = true; }
    profLoaded = true; if (location.hash === "#compte") renderAccount();
  }
  function profileHtml(){
    if (!profLoaded) return `<div class="panel"><h3 class="sec">Mon profil joueur</h3><div class="body acc"><p class="hint">Chargement…</p></div></div>`;
    const P = prof || {}, mine = new Set(P.factions || []), F = FACS(), shown = F.filter(f => mine.has(f));
    return `<div class="panel"><h3 class="sec">Mon profil joueur</h3><div class="body acc">
      <p class="hint">Pour la carte communautaire : trouve des joueurs et des clubs près de chez toi. Ce profil est le même que sur WarCounter et SpearCounter.</p>
      <label class="lbl" for="pf-pseudo">Pseudo</label><input id="pf-pseudo" maxlength="30" value="${esc(P.pseudo || "")}" autocomplete="nickname">
      <label class="lbl" for="pf-city">Ville</label>
      <div class="pf-cityw"><input id="pf-city" value="${esc(profCity ? profCity.city : "")}" autocomplete="off" placeholder="Tape le nom de ta commune"><div id="pf-sug" class="pf-sug" hidden></div></div>
      <label class="lbl" for="pf-club">Club / Association (facultatif)</label>
      <div class="pf-cityw"><input id="pf-club" maxlength="60" value="${esc(P.club || "")}" autocomplete="off" placeholder="Tape le nom : rejoins un club existant ou crée le tien"><div id="pf-csug" class="pf-sug" hidden></div></div>
      <details class="pf-fold"${shown.length ? "" : " open"}><summary><span class="lbl">Gangs Necromunda joués</span><span class="pf-count">${shown.length ? esc(shown.join(", ")) : "Aucune"}</span></summary>
      <div class="pf-facs">${F.map(f => `<label><input type="checkbox" class="pf-fac" value="${esc(f)}"${mine.has(f) ? " checked" : ""}> ${esc(f)}</label>`).join("")}</div></details>
      <label class="pf-vis"><input type="checkbox" id="pf-vis"${P.visible ? " checked" : ""}> <span><b>Apparaître sur la carte communautaire</b><br>Seuls ton pseudo, ta ville, ton club et tes factions ou gangs seront visibles. Jamais ton e-mail.</span></label>
      <button type="button" class="btn primary" id="pf-save"${accBusy ? " disabled" : ""}>Enregistrer mon profil</button>
    </div></div>`;
  }
  async function saveProfile(){
    const pseudo = ($("pf-pseudo").value || "").trim(), club = ($("pf-club").value || "").trim(), vis = $("pf-vis").checked;
    const F = new Set(FACS()), keep = ((prof && prof.factions) || []).filter(f => !F.has(f));   // factions choisies sur WarCounter et SpearCounter conservées
    const factions = keep.concat([...document.querySelectorAll(".pf-fac:checked")].map(x => x.value));
    if (($("pf-city").value || "").trim() === "") profCity = null;
    if (pseudo.length < 2) { accMsg = "Choisis un pseudo d'au moins 2 caractères."; accErr = true; renderAccount(); return; }
    if (vis && !profCity) { accMsg = "Pour apparaître sur la carte, choisis ta ville dans la liste proposée."; accErr = true; renderAccount(); return; }
    accBusy = true;
    try {
      if (!(await fresh())) throw new Error("Session expirée, reconnecte-toi.");
      const C = await resolveClub(club); profClub = C;
      const row = {user_id:sess.uid, pseudo, club:C ? C.name : null, club_id:C ? C.id : null, factions, visible:vis, updated_at:new Date().toISOString(),
        city:profCity ? profCity.city : null, insee:profCity ? profCity.insee : null, lat:profCity ? profCity.lat : null, lng:profCity ? profCity.lng : null};
      await api("/rest/v1/profiles", {method:"POST", headers:{Prefer:"resolution=merge-duplicates,return=minimal"}, body:JSON.stringify(row)});
      prof = row; accMsg = vis ? "Profil enregistré : tu apparaîtras sur la carte." : "Profil enregistré (non visible sur la carte)."; accErr = false;
    } catch(e) { accMsg = /duplicate|unique|23505/i.test(e.message) ? "Ce pseudo est déjà pris, choisis-en un autre." : "Enregistrement impossible : " + frMsg(e.message); accErr = true; }
    accBusy = false; renderAccount(); window.scrollTo(0, 0);
  }
  async function citySuggest(q){
    const box = $("pf-sug"); if (!box) return;
    if (q.length < 2) { box.hidden = true; return; }
    try {
      const r = await fetch(`https://geo.api.gouv.fr/communes?nom=${encodeURIComponent(q)}&fields=nom,code,centre,departement&boost=population&limit=6`);
      const L = await r.json();
      box.innerHTML = L.map(c => `<button type="button" data-city="${esc(JSON.stringify({city:c.nom + (c.departement ? " (" + c.departement.code + ")" : ""), insee:c.code, lat:c.centre ? c.centre.coordinates[1] : null, lng:c.centre ? c.centre.coordinates[0] : null}))}">${esc(c.nom)}${c.departement ? ` <small>${esc(c.departement.nom)} (${esc(c.departement.code)})</small>` : ""}</button>`).join("") || `<p class="hint">Aucune commune trouvée.</p>`;
      box.hidden = false;
    } catch(e) { box.innerHTML = `<p class="hint">Recherche de ville indisponible (connexion ?).</p>`; box.hidden = false; }
  }

  // ---------- Carte communautaire (Leaflet + OpenStreetMap, chargés à la demande) ----------
  let mapObj = null;
  function loadLeaflet(){
    if (window.L) return Promise.resolve();
    return new Promise((ok, ko) => {
      const css = document.createElement("link"); css.rel = "stylesheet"; css.href = "https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.min.css"; document.head.appendChild(css);
      const js = document.createElement("script"); js.src = "https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.min.js"; js.onload = ok; js.onerror = ko; document.head.appendChild(js);
    });
  }
  const mapHtml = () => `<div class="mapw"><p class="hint">Les joueurs qui ont choisi d'apparaître sur la carte, regroupés par ville. Pour y figurer : <a href="#compte">Mon compte</a>, puis Mon profil joueur.</p>
    <p class="map-total" id="map-info" aria-live="polite">Chargement des joueurs…</p>
    <div id="map" class="map"></div></div>`;
  async function renderMap(){
    $("view").innerHTML = mapHtml();
    // 1. Les joueurs et le total, même si le fond de carte ne charge pas
    let rows = [], failed = false;
    try { rows = await api("/rest/v1/profiles?select=pseudo,city,lat,lng,club,factions&visible=eq.true&lat=not.is.null&limit=2000", {}, !!sess); }
    catch(e) { failed = true; }
    if (!$("map")) return;
    const R = rows, by = {};
    R.forEach(r => { const k = r.lat.toFixed(4) + "," + r.lng.toFixed(4); (by[k] = by[k] || {lat:r.lat, lng:r.lng, city:r.city, P:[]}).P.push(r); });
    const clubs = new Set(R.map(r => r.club).filter(Boolean)), nv = Object.keys(by).length;
    $("map-info").innerHTML = failed ? "Joueurs indisponibles : vérifie ta connexion à Internet."
      : `<b>${R.length}</b> joueur${R.length > 1 ? "s" : ""} sur la carte<small>${nv} ville${nv > 1 ? "s" : ""} · ${clubs.size} club${clubs.size > 1 ? "s" : ""}</small>`;
    // 2. Le fond de carte
    try { await loadLeaflet(); } catch(e) { if ($("map")) $("map").innerHTML = `<p class="hint">Carte indisponible : vérifie ta connexion à Internet.</p>`; return; }
    if (!$("map")) return;
    if (mapObj) { mapObj.remove(); mapObj = null; }
    const me = prof && prof.lat ? [prof.lat, prof.lng] : null;
    mapObj = L.map("map", {scrollWheelZoom:true}).setView(me || [46.6, 2.4], me ? 9 : 5);
    L.tileLayer("https://tile.openstreetmap.org/{z}/{x}/{y}.png", {maxZoom:18, attribution:'&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'}).addTo(mapObj);
    Object.values(by).forEach(g => {
      const n = g.P.length;
      L.circleMarker([g.lat, g.lng], {radius:7 + Math.min(n, 10) * 1.5, color:"#d3bfad", weight:2, fillColor:"#7a3b22", fillOpacity:.85}).addTo(mapObj)
        .bindPopup(`<b>${esc(g.city || "")}</b> · ${n} joueur${n > 1 ? "s" : ""}<br>` + g.P.map(p => `<div class="mp"><b>${esc(p.pseudo)}</b>${p.club ? ` · ${esc(p.club)}` : ""}${(p.factions || []).length ? `<br><small>${esc(p.factions.join(", "))}</small>` : ""}</div>`).join(""));
    });
    if (!me && R.length) mapObj.fitBounds(L.latLngBounds(R.map(r => [r.lat, r.lng])).pad(.2), {maxZoom:9});
  }

  // ---------- Page Mon compte ----------
  function accountHtml(){
    const m = ls.get(SK.meta) || {};
    const msg = accMsg ? `<p class="acc-msg${accErr ? " err" : ""}">${esc(accMsg)}</p>` : "";
    if (sess) return `<div class="sup-hero"><h2>Mon compte</h2><p>Connecté avec <b>${esc(sess.email || "")}</b></p></div>${msg}
      <div class="panel"><div class="body acc">
        <p>Tes gangs, ta partie en cours et ton historique sont synchronisés automatiquement sur tous les appareils où tu es connecté.</p>
        <p class="hint">Ce compte vaut pour les trois apps : NecroCounter, WarCounter et SpearCounter.</p>
        <p class="hint">${m.dirty ? "Modifications en attente d'envoi." : m.at ? "Dernière synchronisation : " + new Date(m.at).toLocaleString("fr-FR") : ""}</p>
        <button type="button" class="btn primary" id="acc-sync"${accBusy ? " disabled" : ""}>Synchroniser maintenant</button>
        <button type="button" class="btn" id="acc-out">Se déconnecter</button>
      </div></div>
      ${profileHtml()}
      <div class="panel"><div class="body acc">
        <p class="hint"><b class="acc-warn">Attention !</b> Supprimer ton compte efface définitivement tes données sur le serveur, pour NecroCounter, WarCounter et SpearCounter. Les données de cet appareil sont conservées.</p>
        <button type="button" class="btn danger" id="acc-del">${delArmed ? "Confirmer la suppression définitive" : "Supprimer mon compte"}</button>
      </div></div>
      <p class="sup-thanks"><a href="#confidentialite">Confidentialité et données personnelles</a></p>`;
    return `<div class="sup-hero"><h2>Mon compte</h2><p>Facultatif : sans compte, l'app fonctionne comme avant.<br>Avec un compte, tu retrouves tes gangs et tes parties sur tous tes appareils.<br><b>Un seul compte pour les trois apps</b> : NecroCounter, WarCounter et SpearCounter. Tu as déjà un compte sur l'une d'elles ? Utilise le même e-mail et le même mot de passe.</p></div>${msg}
      <div class="panel"><div class="body acc">
        <label class="lbl" for="acc-mail">E-mail</label><input type="email" id="acc-mail" autocomplete="email" inputmode="email">
        <label class="lbl" for="acc-pass">Mot de passe (6 caractères minimum)</label><input type="password" id="acc-pass" autocomplete="current-password">
        <button type="button" class="btn primary" id="acc-in"${accBusy ? " disabled" : ""}>Se connecter</button>
        <button type="button" class="btn" id="acc-up"${accBusy ? " disabled" : ""}>Créer un compte</button>
        <p class="hint">À la première connexion, les gangs et les parties de cet appareil sont ajoutés à ton compte.</p>
      </div></div>
      <p class="sup-thanks"><a href="#confidentialite">Confidentialité et données personnelles</a></p>`;
  }
  function renderAccount(){ $("view").innerHTML = accountHtml(); if (sess && !profLoaded) loadProfile(); }
  async function accAuth(signup){
    const email = ($("acc-mail").value || "").trim(), password = $("acc-pass").value || "";
    if (!email || !password) { accMsg = "Indique ton e-mail et ton mot de passe."; accErr = true; renderAccount(); return; }
    accBusy = true; accMsg = ""; renderAccount();
    try {
      const j = signup ? await api("/auth/v1/signup", {method:"POST", body:JSON.stringify({email, password})}, false)
                       : await api("/auth/v1/token?grant_type=password", {method:"POST", body:JSON.stringify({email, password})}, false);
      if (!j || !j.access_token) { accMsg = "Compte créé, mais il doit être confirmé avant la connexion."; accErr = true; }
      else { setSess(j); accBusy = false; accMsg = "Connexion réussie, synchronisation…"; accErr = false; renderAccount(); await sync(true); return; }
    } catch(e) { accMsg = frMsg(e.message); accErr = true; }
    accBusy = false; renderAccount();
  }
  const privacyHtml = () => `<div class="sup-hero"><h2>Confidentialité</h2><p>Ce que NecroCounter fait de tes données.</p></div>
    <div class="panel"><div class="body"><dl class="blk">
      <dt><b>Sans compte</b></dt><dd>Tes gangs et tes parties restent uniquement sur ton appareil. Rien n'est envoyé.</dd>
      <dt><b>Avec un compte (facultatif)</b></dt><dd>Sont enregistrés : ton adresse e-mail, ton mot de passe (chiffré, jamais lisible), tes gangs, ta partie en cours et ton historique. Ils servent uniquement à te connecter et à synchroniser tes données entre tes appareils. Le compte est commun à NecroCounter, WarCounter et SpearCounter.</dd>
      <dt><b>Profil joueur (facultatif)</b></dt><dd>Pseudo, ville (centre de la commune, jamais d'adresse), club et factions ou gangs joués. Ils ne sont visibles des autres joueurs que si tu coches « Apparaître sur la carte communautaire », et tu peux décocher à tout moment.</dd>
      <dt><b>Hébergement</b></dt><dd>Supabase, sur des serveurs situés dans l'Union européenne.</dd>
      <dt><b>Durée de conservation</b></dt><dd>Jusqu'à la suppression de ton compte.</dd>
      <dt><b>Tes droits</b></dt><dd>Tu peux supprimer ton compte et toutes tes données en ligne à tout moment depuis la page Mon compte. Pour toute question (accès, rectification, suppression) : warcounter@proton.me.</dd>
      <dt><b>Ce qu'on ne fait pas</b></dt><dd>Aucune publicité, aucune revente, aucun partage de tes données. La mesure d'audience (GoatCounter) est anonyme et sans cookie.</dd>
      <dt><b>Responsable</b></dt><dd>elcounter, éditeur de NecroCounter, WarCounter et SpearCounter (warcounter@proton.me).</dd>
    </dl></div></div>`;

  // ---------- Événements ----------
  document.addEventListener("input", e => {
    if (e.target.id === "pf-club") { profClub = null; clearTimeout(clubT); const q = e.target.value.trim(); clubT = setTimeout(() => clubSuggest(q), 300); return; }
    if (e.target.id === "pf-city") { profCity = null; clearTimeout(cityT); const q = e.target.value.trim(); cityT = setTimeout(() => citySuggest(q), 300); }
  });
  document.addEventListener("click", async e => {
    if (location.hash !== "#compte") return;
    const id = e.target.id;
    if (id === "acc-in" || id === "acc-up") { accAuth(id === "acc-up"); return; }
    if (id === "pf-save") { saveProfile(); return; }
    const kb = e.target.closest("[data-club]");
    if (kb) { profClub = JSON.parse(kb.dataset.club); $("pf-club").value = profClub.name; $("pf-csug").hidden = true; return; }
    const cb = e.target.closest("[data-city]");
    if (cb) { profCity = JSON.parse(cb.dataset.city); $("pf-city").value = profCity.city; $("pf-sug").hidden = true; return; }
    if (id === "acc-sync") { accBusy = true; renderAccount(); clearTimeout(pushT); try { if (await fresh()) await push(); accMsg = "Synchronisé."; accErr = false; } catch(x) { accMsg = "Synchronisation impossible : " + frMsg(x.message); accErr = true; } accBusy = false; renderAccount(); return; }
    if (id === "acc-out") { try { await api("/auth/v1/logout", {method:"POST"}); } catch(x) {} clearSess(); prof = null; profLoaded = false; profCity = null; accMsg = "Tu es déconnecté. Tes données restent sur cet appareil."; accErr = false; delArmed = false; renderAccount(); return; }
    if (id === "acc-del") {
      if (!delArmed) { delArmed = true; renderAccount(); return; }
      try { if (await fresh()) await api("/rest/v1/rpc/delete_my_account", {method:"POST", body:"{}"}); clearSess(); prof = null; profLoaded = false; profCity = null; accMsg = "Ton compte et tes données en ligne ont été supprimés."; accErr = false; }
      catch(x) { accMsg = "Suppression impossible : " + frMsg(x.message); accErr = true; }
      delArmed = false; renderAccount();
    }
  });

  window.NC_COMPTE = {
    open(view){
      if (view === "compte") { delArmed = false; renderAccount(); }
      else if (view === "carte") { if (sess && !profLoaded) loadProfile().then(() => { if (location.hash === "#carte") renderMap(); }); else renderMap(); }
      else if (view === "confidentialite") $("view").innerHTML = privacyHtml();
    },
    get connected(){ return !!sess; }
  };
})();
