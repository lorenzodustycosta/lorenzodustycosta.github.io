// Pulsante chiaro/scuro.
// Il tema di default è lo scuro (definito nel CSS, funziona anche senza JavaScript):
// questo script aggiunge solo la possibilità di passare al chiaro e ricordarlo.

const root = document.documentElement;
const button = document.querySelector(".theme-toggle");

// Tema attivo: quello scelto a mano (attributo data-theme), altrimenti lo scuro di default
function activeTheme() {
  return root.dataset.theme || "dark";
}

function updateButton() {
  button.setAttribute("aria-pressed", String(activeTheme() === "dark"));
}

button.addEventListener("click", () => {
  const next = activeTheme() === "dark" ? "light" : "dark";
  root.dataset.theme = next;
  try {
    localStorage.setItem("theme", next);
  } catch {
    // localStorage può non essere disponibile (es. navigazione privata): il tema vale solo per questa pagina
  }
  updateButton();
});

updateButton();
button.hidden = false;
