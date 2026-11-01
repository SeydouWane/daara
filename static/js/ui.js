// Comportements d'interface, en amélioration progressive : sans JavaScript, tout reste
// utilisable grâce aux éléments <details>.
//  - Menus déroulants (details[data-menu]) : un seul ouvert à la fois, fermeture au clic
//    extérieur et avec Échap (le focus revient sur le bouton du menu).
//  - Sidebar de l'espace (details[data-sidebar]) : replié sur petit écran, toujours
//    ouvert sur grand écran.
(() => {
  const menus = () => document.querySelectorAll("details[data-menu][open]");
  const closeAll = (except) => {
    for (const menu of menus()) {
      if (menu !== except && !menu.contains(except)) menu.open = false;
    }
  };

  // L'événement toggle ne remonte pas : on l'écoute en phase de capture.
  document.addEventListener(
    "toggle",
    (event) => {
      if (event.target.matches?.("details[data-menu]") && event.target.open) {
        closeAll(event.target);
      }
    },
    true,
  );

  document.addEventListener("click", (event) => {
    if (!event.target.closest("details[data-menu]")) closeAll();
  });

  document.addEventListener("keydown", (event) => {
    if (event.key !== "Escape") return;
    const current = event.target.closest?.("details[data-menu][open]");
    closeAll();
    current?.querySelector("summary")?.focus();
  });

  // Boutons « Copier » (button[data-copy="#cible"]) : affichés seulement si le presse-papiers
  // est disponible ; le libellé confirme la copie quelques secondes.
  if (navigator.clipboard) {
    for (const button of document.querySelectorAll("button[data-copy]")) {
      button.hidden = false;
      const label = button.textContent;
      button.addEventListener("click", async () => {
        const target = document.querySelector(button.dataset.copy);
        if (!target) return;
        await navigator.clipboard.writeText(target.textContent.trim());
        button.textContent = button.dataset.copied || label;
        setTimeout(() => {
          button.textContent = label;
        }, 2500);
      });
    }
  }

  const sidebar = document.querySelector("details[data-sidebar]");
  if (sidebar) {
    const wide = window.matchMedia("(min-width: 768px)");
    const sync = () => {
      sidebar.open = wide.matches;
    };
    sync();
    wide.addEventListener("change", sync);
  }
})();
