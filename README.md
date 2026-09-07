# ICON-EU 7 km — Alertes-météo

Module indépendant de prévisions météo horaires par commune en France métropolitaine.

- **Modèle réellement sélectionné : ICON-EU**, via `models=icon_eu` sur l’API DWD d’Open-Meteo.
- Température à 2 m, précipitations, vent à 10 m et rafales.
- Jusqu’à cinq jours, selon disponibilité ; choix du jour et recherche de commune.
- Horaires de Paris, erreurs explicites et données manquantes signalées.

## Télécharger le ZIP

Le ZIP prêt à extraire est disponible dans les **[Releases](https://github.com/alertesmeteo-hub/ICON-EU-7-km/releases/latest)**.
Le bouton **Code → Download ZIP** télécharge également les sources.

## Démarrer

Prérequis : Node.js 22.13 ou supérieur et pnpm.

```sh
pnpm install
pnpm dev
```

Ouvrir l’adresse locale affichée. Le module se trouve directement à la racine `/`.

```sh
pnpm lint
pnpm build
pnpm start
```

Le projet utilise React, TypeScript, Vinext, Vite et Cloudflare Workers. `pnpm start` lance l’aperçu local du Worker compilé. Adapter le déploiement à votre hébergement.

**Ce ZIP contient une application React ; ce n’est pas une extension WordPress à téléverser dans Extensions.** Aucun fichier `.env.local` ni aucune clé Météo-France n’est nécessaire pour cette version.

## Données

Source : DWD via [Open-Meteo](https://open-meteo.com/en/docs/dwd-api).
La grille ICON-EU est d’environ 7 km. Au-delà de 78 heures, les valeurs horaires sont interpolées à partir de pas de 3 heures. L’heure de consultation affichée n’est pas l’heure de calcul du modèle.

L’accès gratuit Open-Meteo est destiné aux usages non commerciaux. Pour une exploitation commerciale, utiliser une offre adaptée et modifier la connexion selon ses conditions : [conditions Open-Meteo](https://open-meteo.com/en/terms).

Ce dépôt est dédié à ICON-EU ; il ne contient ni le guide des villes ni le module AROME-IFS.
