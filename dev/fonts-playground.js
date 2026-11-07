// Font playground (solo sviluppo, non finisce nel sito pubblicato).
// Ogni controllo del pannello aggiorna una variabile CSS su <html>; lo stato
// completo viene scritto nell'URL, così una combinazione si può salvare o condividere.

const root = document.documentElement;
const form = document.querySelector(".pg-form");
const status = document.querySelector(".pg-status");

// Pesi disponibili su Google Fonts: chiedere un peso che non esiste fa fallire il caricamento
const range = (from, to) => Array.from({ length: (to - from) / 100 + 1 }, (_, i) => from + i * 100);

// [nome, categoria, pesi disponibili, ha il corsivo]
const FONTS = {
  heading: [
    ["Fraunces", "serif", range(300, 800), true],
    ["Newsreader", "serif", range(300, 800), true],
    ["Source Serif 4", "serif", range(300, 800), true],
    ["Literata", "serif", range(300, 800), true],
    ["Spectral", "serif", range(300, 800), true],
    ["IBM Plex Serif", "serif", range(300, 700), true],
    ["Instrument Serif", "serif", [400], true],
    ["Young Serif", "serif", [400], false],
    ["Schibsted Grotesk", "sans-serif", range(400, 800), true],
    ["Bricolage Grotesque", "sans-serif", range(300, 800), false],
    ["Familjen Grotesk", "sans-serif", range(400, 700), true],
  ],
  body: [
    ["Source Serif 4", "serif", range(300, 800), true],
    ["Newsreader", "serif", range(300, 800), true],
    ["Literata", "serif", range(300, 800), true],
    ["Spectral", "serif", range(300, 800), true],
    ["IBM Plex Serif", "serif", range(300, 700), true],
    ["Crimson Pro", "serif", range(300, 800), true],
    ["IBM Plex Sans", "sans-serif", range(300, 700), true],
    ["Public Sans", "sans-serif", range(300, 800), true],
    ["Schibsted Grotesk", "sans-serif", range(400, 800), true],
    ["Instrument Sans", "sans-serif", range(400, 700), true],
    ["Atkinson Hyperlegible", "sans-serif", [400, 700], true],
    ["Libre Franklin", "sans-serif", range(300, 800), true],
  ],
  mono: [
    ["IBM Plex Mono", "monospace", range(300, 700), false],
    ["JetBrains Mono", "monospace", range(300, 800), false],
    ["DM Mono", "monospace", [300, 400, 500], false],
    ["Source Code Pro", "monospace", range(300, 800), false],
    ["Martian Mono", "monospace", range(300, 800), false],
    ["Spline Sans Mono", "monospace", range(300, 700), false],
  ],
};

// Pesi da caricare per ogni ruolo: i titoli tutti (c'è lo slider), testo e mono solo quelli usati da main.css
const WANTED = { heading: null, body: [400, 600, 700], mono: [400, 500, 700] };

// Campo del form -> ruolo del font
const ROLES = { h: "heading", b: "body", m: "mono" };

// Default = font di produzione (main.css)
const DEFAULTS = { h: "Source Serif 4", b: "IBM Plex Sans", m: "IBM Plex Mono", s: "17", lh: "1.6", hw: "600" };

function findFont(role, name) {
  return FONTS[role].find(([fontName]) => fontName === name) || FONTS[role][0];
}

// Valore CSS di font-family, con il fallback generico della categoria
function fontStack([name, category]) {
  return `"${name}", ${category}`;
}

// Aggiunge il <link> di Google Fonts per un font, una sola volta per combinazione font+pesi.
// Formato dell'API: family=Nome+Font:ital,wght@0,400;0,700;1,400
const loaded = new Set();
function loadFont(role, font) {
  const [name, , available, hasItalic] = font;
  const wanted = WANTED[role];
  let weights = wanted ? available.filter((w) => wanted.includes(w)) : available;
  if (weights.length === 0) weights = [available[0]];

  let axes = "wght@" + weights.join(";");
  if (hasItalic) {
    const upright = weights.map((w) => `0,${w}`);
    const italic = weights.includes(400) ? ["1,400"] : [`1,${weights[0]}`];
    axes = "ital,wght@" + [...upright, ...italic].join(";");
  }
  const family = name.replaceAll(" ", "+") + ":" + axes;
  if (loaded.has(family)) return;
  loaded.add(family);

  const link = document.createElement("link");
  link.rel = "stylesheet";
  link.href = `https://fonts.googleapis.com/css2?family=${family}&display=swap`;
  document.head.append(link);
}

// Riempie i tre menu a tendina, separando serif, sans e mono con <optgroup>
function fillSelects() {
  for (const [field, role] of Object.entries(ROLES)) {
    const select = form.elements[field];
    const groups = {};
    for (const [name, category] of FONTS[role]) {
      if (!groups[category]) {
        groups[category] = document.createElement("optgroup");
        groups[category].label = category;
        select.append(groups[category]);
      }
      groups[category].append(new Option(name, name));
    }
  }
}

// Tema attivo: quello scelto (data-theme), altrimenti lo scuro di default, come in theme.js
function isDark() {
  return (root.dataset.theme || "dark") === "dark";
}

// Legge lo stato dall'URL, con i valori di default per i parametri mancanti
function readState() {
  const params = new URLSearchParams(location.search);
  const state = { ...DEFAULTS };
  for (const key of Object.keys(DEFAULTS)) {
    if (params.has(key)) state[key] = params.get(key);
  }
  if (params.has("t")) state.t = params.get("t");
  return state;
}

// Porta lo stato nei controlli del form
function showState(state) {
  for (const field of Object.keys(ROLES)) {
    form.elements[field].value = findFont(ROLES[field], state[field])[0];
  }
  form.elements.s.value = state.s;
  form.elements.lh.value = state.lh;
  form.elements.hw.value = state.hw;
  form.elements.t.checked = state.t ? state.t === "dark" : isDark();
}

// Applica i controlli alla pagina: font, variabili CSS, tema e URL
function apply() {
  const el = form.elements;
  const fonts = {};
  for (const [field, role] of Object.entries(ROLES)) {
    fonts[role] = findFont(role, el[field].value);
    loadFont(role, fonts[role]);
  }

  for (const [role, variable] of [["heading", "--font-heading"], ["body", "--font-body"], ["mono", "--font-mono"]]) {
    root.style.setProperty(variable, fontStack(fonts[role]));
  }
  root.style.setProperty("--text-base", `${el.s.value / 16}rem`);
  root.style.setProperty("--leading", el.lh.value);
  root.style.setProperty("--heading-weight", el.hw.value);
  root.dataset.theme = el.t.checked ? "dark" : "light";

  el["s-out"].value = `${el.s.value}px`;
  el["lh-out"].value = el.lh.value;
  el["hw-out"].value = el.hw.value;
  // Avvisa se il peso scelto non esiste per il font dei titoli (il browser usa il più vicino)
  status.textContent = fonts.heading[2].includes(Number(el.hw.value))
    ? ""
    : `${fonts.heading[0]}: peso ${el.hw.value} non disponibile.`;

  // replaceState: aggiorna l'URL senza riempire la cronologia del browser
  const params = new URLSearchParams({
    h: el.h.value, b: el.b.value, m: el.m.value,
    s: el.s.value, lh: el.lh.value, hw: el.hw.value,
    t: el.t.checked ? "dark" : "light",
  });
  history.replaceState(null, "", `${location.pathname}?${params}${location.hash}`);
}

// Le variabili della combinazione corrente, pronte da incollare in main.css
function cssText() {
  const style = getComputedStyle(root);
  const names = ["--font-heading", "--font-body", "--font-mono", "--text-base", "--leading", "--heading-weight"];
  const lines = names.map((name) => `  ${name}: ${style.getPropertyValue(name)};`);
  return `:root {\n${lines.join("\n")}\n}\n`;
}

async function copyCss() {
  const text = cssText();
  try {
    await navigator.clipboard.writeText(text);
    status.textContent = "CSS copiato.";
  } catch {
    // Clipboard API non disponibile (es. permessi negati): mostra il testo da copiare a mano
    window.prompt("Copia il CSS:", text);
  }
}

fillSelects();
showState(readState());
apply();

form.addEventListener("input", apply);
form.addEventListener("submit", (event) => event.preventDefault());
form.querySelector('[data-action="copy"]').addEventListener("click", copyCss);
form.querySelector('[data-action="reset"]').addEventListener("click", () => {
  showState({ ...DEFAULTS });
  apply();
});

// Su schermi stretti il pannello parte chiuso, per lasciare spazio ai contenuti
const compactPanel = window.matchMedia("(max-width: 63.99rem)");
const panel = document.querySelector(".pg-panel");
panel.open = !compactPanel.matches;
compactPanel.addEventListener("change", () => { panel.open = !compactPanel.matches; });

// Apre i <details> delle sezioni marcate, per vedere anche i testi dei dettagli
for (const details of document.querySelectorAll("[data-pg-open] details")) {
  details.open = true;
}

// Mantiene il pannello allineato anche quando si usa il toggle dell'header.
new MutationObserver(() => {
  form.elements.t.checked = isDark();
  const params = new URLSearchParams(location.search);
  params.set("t", isDark() ? "dark" : "light");
  history.replaceState(null, "", `${location.pathname}?${params}${location.hash}`);
}).observe(root, { attributes: true, attributeFilter: ["data-theme"] });
window.addEventListener("popstate", () => { showState(readState()); apply(); });
