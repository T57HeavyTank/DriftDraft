// Lingua dell'interfaccia (2026-10-19).
//
// DriftDraft e' scritto in italiano e RESTA scritto in italiano: app.js, index.html
// e i messaggi del server non sono stati toccati per la traduzione. Questo file
// osserva la pagina e, se la lingua scelta non e' l'italiano, sostituisce i testi
// mentre vengono inseriti (prima che il browser li disegni: le callback di un
// MutationObserver girano prima del paint, niente lampi di italiano).
//
// Perche' cosi' e non con t("...") sparso ovunque: i testi italiani sono ~500, in
// 6500 righe di app.js piu' i messaggi Python. Avvolgerli uno per uno avrebbe
// toccato quasi ogni funzione dell'interfaccia per una richiesta che non ne cambia
// il comportamento, e in italiano qualunque svista sarebbe diventata un bug. Cosi'
// in italiano questo file non fa niente, e in inglese il peggio che puo' succedere
// e' una frase rimasta in italiano.
//
// Il dizionario e' web/lang/en.json, uno solo per interfaccia e server: la chiave
// e' il testo italiano esatto (spazi compressi). Tre tipi di voce:
//   - "testi" senza segnaposto: confronto esatto;
//   - "testi" con {0}, {1}...: i template di app.js e le f-string Python. Quel
//     che finisce nei segnaposto viene a sua volta tradotto se e' una voce nota
//     (un nome di comp dentro una frase, un pezzo opzionale come ", tier S");
//   - "frammenti": pezzi sostituiti OVUNQUE compaiano, per le frasi composte a
//     pezzi a seconda del caso (le ragioni dei suggerimenti).
// Una frase con " · ", " — ", "; " o " - " che non e' una voce intera si traduce
// pezzo per pezzo (i motivi dei ban suggeriti, per esempio, sono uniti da "; ").
//
// ATTENZIONE per chi aggiunge codice: non decidere mai qualcosa leggendo il testo
// visibile di un elemento (textContent, title...). In inglese li' c'e' l'inglese.
// Il dato va tenuto da parte (dataset, variabile) - vedi bindTagFilterClick.
//
// Le frasi nuove non presenti nel dizionario restano in italiano e finiscono in
// window.i18nMissing: aprendo l'app in inglese e girando le schermate, quell'insieme
// e' l'elenco di cosa manca da tradurre.
(function () {
  const LANG_KEY = "lang";
  const LINGUE = ["it", "en"];

  function linguaIniziale() {
    try {
      const scelta = localStorage.getItem(LANG_KEY);
      if (LINGUE.includes(scelta)) return scelta;
    } catch (e) {
      // storage non disponibile: si segue il sistema
    }
    // La prima volta si segue la lingua di Windows: italiano su un pc
    // italiano, inglese ovunque altro.
    return (navigator.language || "it").toLowerCase().startsWith("it") ? "it" : "en";
  }

  const LANG = linguaIniziale();
  window.APP_LANG = LANG;
  document.documentElement.lang = LANG;

  const esatte = new Map();
  const modelli = [];
  const frammenti = [];
  const prodotti = new Set(); // testi gia' tradotti: non vanno ritradotti ne' segnalati
  const mancanti = new Set();
  window.i18nMissing = mancanti;

  const norm = (s) => s.replace(/\s+/g, " ").trim();
  const escape = (s) => s.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");

  function compila(chiave, en, ancorato) {
    const parti = chiave.split(/(\{\d+\})/);
    const ordine = [];
    let src = "";
    let fisso = "";
    for (const p of parti) {
      const m = p.match(/^\{(\d+)\}$/);
      if (m) {
        ordine.push(Number(m[1]));
        src += "([\\s\\S]*?)";
      } else {
        src += escape(p);
        if (p.length > fisso.length) fisso = p;
      }
    }
    return {
      re: new RegExp(ancorato ? `^${src}$` : src, ancorato ? "" : "g"),
      ordine,
      en,
      fisso, // il pezzo fisso piu' lungo: se manca nel testo, inutile provare la regex
    };
  }

  if (LANG !== "it") {
    try {
      // Sincrono apposta: app.js parte subito dopo e deve trovare il dizionario
      // pronto. E' un file locale servito dall'app stessa, pochi millisecondi.
      const xhr = new XMLHttpRequest();
      xhr.open("GET", `/web/lang/${LANG}.json`, false);
      xhr.send();
      if (xhr.status === 200) {
        const diz = JSON.parse(xhr.responseText);
        for (const [it, en] of Object.entries(diz.testi || {})) {
          const k = norm(it);
          if (/\{\d+\}/.test(k)) modelli.push(compila(k, en, true));
          else esatte.set(k, en);
          prodotti.add(norm(en));
        }
        for (const [it, en] of Object.entries(diz.frammenti || {})) {
          frammenti.push(compila(it, en, false));
        }
        // Prima i modelli piu' specifici: a parita' di testo vince quello con
        // piu' parte fissa (un "{0} draft" non deve mangiarsi frasi piu' lunghe).
        modelli.sort((a, b) => b.fisso.length - a.fisso.length);
      }
    } catch (e) {
      // Senza dizionario l'app resta in italiano: meglio che non partire.
    }
  }

  const haParole = (s) => /[A-Za-zÀ-ÿ]{2}/.test(s);

  function riempi(modello, gruppi, profondita) {
    return modello.en.replace(/\{(\d+)\}/g, (_, i) => {
      const pos = modello.ordine.indexOf(Number(i));
      const valore = pos === -1 ? "" : gruppi[pos] ?? "";
      return traduciParte(valore, profondita + 1);
    });
  }

  function traduciNorm(k, profondita) {
    if (esatte.has(k)) return esatte.get(k);
    if (prodotti.has(k)) return k;
    if (profondita > 4) return null;
    for (const m of modelli) {
      if (m.fisso && !k.includes(m.fisso)) continue;
      const x = k.match(m.re);
      if (x) return riempi(m, x.slice(1), profondita);
    }
    for (const sep of [" · ", " — ", "; ", " - "]) {
      if (!k.includes(sep)) continue;
      const parti = k.split(sep);
      const tradotte = parti.map((p) => (haParole(p) ? traduciNorm(norm(p), profondita + 1) : p));
      if (tradotte.some((t, i) => t !== null && t !== parti[i])) {
        return tradotte.map((t, i) => (t === null ? parti[i] : t)).join(sep);
      }
    }
    let cambiato = false;
    let out = k;
    for (const f of frammenti) {
      if (f.fisso && !out.includes(f.fisso)) continue;
      f.re.lastIndex = 0;
      out = out.replace(f.re, (...g) => {
        cambiato = true;
        return riempi(f, g.slice(1, 1 + f.ordine.length), profondita);
      });
    }
    return cambiato ? out : null;
  }

  function traduciParte(v, profondita) {
    const k = norm(v);
    if (!k || !haParole(k)) return v;
    const r = traduciNorm(k, profondita);
    if (r === null) return v;
    return v.match(/^\s*/)[0] + r + v.match(/\s*$/)[0];
  }

  // Traduce un testo qualsiasi; senza traduzione lo restituisce identico.
  function t(testo) {
    if (LANG === "it" || typeof testo !== "string" || !testo) return testo;
    const k = norm(testo);
    if (!k || !haParole(k)) return testo;
    let r = traduciNorm(k, 0);
    if (r === null && testo.includes("\n")) {
      // Tooltip su piu' righe: riga per riga, gli a capo restano dove sono.
      const righe = testo.split("\n");
      const tradotte = righe.map((riga) => traduciParte(riga, 1));
      if (tradotte.some((x, i) => x !== righe[i])) {
        tradotte.forEach((x, i) => {
          if (x === righe[i] && haParole(righe[i])) mancanti.add(norm(righe[i]));
        });
        const out = tradotte.join("\n");
        prodotti.add(norm(out));
        return out;
      }
    }
    if (r === null) {
      mancanti.add(k);
      return testo;
    }
    prodotti.add(norm(r));
    return testo.match(/^\s*/)[0] + r + testo.match(/\s*$/)[0];
  }
  window.t = t;

  if (LANG === "it") return;

  // ---------------------------------------------------------------- la pagina
  const ATTRIBUTI = ["title", "placeholder", "aria-label", "alt"];
  const SALTA = new Set(["SCRIPT", "STYLE", "TEXTAREA", "INPUT"]);

  function traduciNodo(n) {
    if (n.nodeType === Node.TEXT_NODE) {
      if (n.parentNode && SALTA.has(n.parentNode.nodeName)) return;
      const v = n.nodeValue;
      const r = t(v);
      if (r !== v) n.nodeValue = r;
      return;
    }
    if (n.nodeType !== Node.ELEMENT_NODE) return;
    // INPUT sta in SALTA per il suo valore (testo dell'utente), ma il
    // placeholder e il title vanno tradotti: si passa dagli attributi e basta.
    if (SALTA.has(n.nodeName) && n.nodeName !== "INPUT") return;
    for (const a of ATTRIBUTI) {
      const v = n.getAttribute(a);
      if (v) {
        const r = t(v);
        if (r !== v) n.setAttribute(a, r);
      }
    }
    if (n.nodeName === "INPUT") return;
    for (const c of n.childNodes) traduciNodo(c);
  }

  traduciNodo(document.body);
  document.title = t(document.title);

  new MutationObserver((mutazioni) => {
    for (const m of mutazioni) {
      if (m.type === "childList") m.addedNodes.forEach(traduciNodo);
      else if (m.type === "characterData") traduciNodo(m.target);
      else if (m.type === "attributes") {
        const v = m.target.getAttribute(m.attributeName);
        if (v) {
          const r = t(v);
          if (r !== v) m.target.setAttribute(m.attributeName, r);
        }
      }
    }
  }).observe(document.body, {
    subtree: true,
    childList: true,
    characterData: true,
    attributes: true,
    attributeFilter: ATTRIBUTI,
  });

  // alert/confirm/prompt: i loro testi non passano dalla pagina.
  const nativi = { alert: window.alert, confirm: window.confirm, prompt: window.prompt };
  window.alert = (msg) => nativi.alert.call(window, t(String(msg ?? "")));
  window.confirm = (msg) => nativi.confirm.call(window, t(String(msg ?? "")));
  window.prompt = (msg, def) => nativi.prompt.call(window, t(String(msg ?? "")), def);
})();

// La riga "Lingua" delle Impostazioni. Si cambia ricaricando la pagina: ogni
// testo gia' a video si rifa' nella lingua nuova, senza stati a meta'.
(function () {
  function collega() {
    for (const lingua of ["it", "en"]) {
      const btn = document.getElementById(`lang-${lingua}`);
      if (!btn) continue;
      btn.classList.toggle("active", window.APP_LANG === lingua);
      btn.addEventListener("click", () => {
        if (window.APP_LANG === lingua) return;
        try {
          localStorage.setItem("lang", lingua);
        } catch (e) {
          return;
        }
        location.reload();
      });
    }
  }
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", collega);
  else collega();
})();
