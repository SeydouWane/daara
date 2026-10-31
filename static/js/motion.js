// Mise en pause des animations décoratives (WCAG 2.2.2) : le logo boucle en continu, chacun doit
// pouvoir l'arrêter. Le choix est mémorisé dans le navigateur. Chargé dans <head> pour appliquer
// la préférence avant le premier affichage.
(() => {
  const KEY = "daara-motion";
  const root = document.documentElement;

  const read = () => {
    try {
      return localStorage.getItem(KEY) === "paused";
    } catch {
      return false;
    }
  };

  const apply = (paused) => {
    root.dataset.motion = paused ? "paused" : "auto";
    const button = document.querySelector("[data-motion-toggle]");
    if (button) button.setAttribute("aria-pressed", String(paused));
  };

  apply(read());

  document.addEventListener("DOMContentLoaded", () => {
    const button = document.querySelector("[data-motion-toggle]");
    if (!button) return;
    button.hidden = false;
    apply(read());
    button.addEventListener("click", () => {
      const paused = root.dataset.motion !== "paused";
      try {
        localStorage.setItem(KEY, paused ? "paused" : "auto");
      } catch {
        // Stockage indisponible (navigation privée) : la pause vaut pour la page en cours.
      }
      apply(paused);
    });
  });
})();
