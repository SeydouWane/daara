#!/bin/sh
# Recompile le CSS dès qu'un gabarit, une feuille ou un module Python change.
# Scrute par interrogation : les dossiers Windows montés dans Docker Desktop
# ne propagent pas les événements de fichiers aux conteneurs.
set -eu

stamp=/tmp/daara-assets.stamp
touch "$stamp"
npm run build

while sleep 1; do
  changed=$(find assets templates apps -newer "$stamp" -type f \
    \( -name '*.html' -o -name '*.css' -o -name '*.py' -o -name '*.js' \) -print 2>/dev/null | head -n 1)
  if [ -n "$changed" ]; then
    touch "$stamp"
    npm run build:css || true
  fi
done
