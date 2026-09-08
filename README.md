# ICON-EU 7 km — GitHub Actions → WordPress

Les prévisions sont préparées automatiquement depuis les **fichiers officiels DWD ICON-EU**, puis publiées dans la branche `data`. Aucune clé météo et aucune API Open-Meteo ne sont nécessaires.

## Lancer le run

1. Ouvrir **[Actions → Mise à jour ICON-EU 7 km](https://github.com/alertesmeteo-hub/ICON-EU-7-km/actions/workflows/update-icon-eu.yml)**.
2. Cliquer **Run workflow**, laisser la branche `main`, puis confirmer.
3. Attendre la coche verte. La première préparation nationale peut prendre plusieurs minutes.
4. Vérifier la branche **[data](https://github.com/alertesmeteo-hub/ICON-EU-7-km/tree/data)**.

La vérification automatique a lieu **toutes les heures, à la minute 43 UTC** (GitHub peut retarder un lancement). Le dernier calcul complet à +120 h est sélectionné parmi les runs 00, 06, 12 et 18 UTC. Si le calcul est déjà publié, aucun téléchargement GRIB ni nouvelle publication n’est effectué. La case `force` reconstruit volontairement le calcul courant.

En cas de données incomplètes, d’erreur de calcul ou de téléchargement, le workflow échoue et conserve la dernière publication valide. Une publication n’est envoyée qu’après vérification des 96 départements et de toutes les communes du catalogue. Aucun écrasement forcé de l’historique Git.

## Installer dans WordPress / Avada

Télécharger **`icon-eu-7-km-wordpress.zip`** dans **[Releases](https://github.com/alertesmeteo-hub/ICON-EU-7-km/releases/latest)** (ou dans les artefacts du dernier run réussi).

1. WordPress → **Extensions → Ajouter → Téléverser une extension**.
2. Installer le ZIP, puis activer **ICON-EU 7 km — Alertes-météo**.
3. Dans Avada, ajouter un bloc texte/code avec :

```text
[icon_eu_meteo]
```

Commune initiale personnalisée :

```text
[icon_eu_meteo code="66136"]
```

Le module propose une recherche par commune ou code postal, un choix du jour, la température, les précipitations, le vent, les rafales et les nuages. Chaque visite charge des JSON préparés sur GitHub, pas des fichiers GRIB.

Le ZIP nommé **wordpress** est une extension installable. Les ZIP de sources React des versions 1.x ne le sont pas.

## Données et précision

- Source : [DWD Open Data ICON-EU](https://opendata.dwd.de/weather/nwp/icon-eu/), grille régulière de 0,0625° (environ 7 km).
- 34 746 communes du catalogue français repris du module AROME ; les indices de grille sont entièrement recalculés pour ICON-EU.
- Point de grille le plus proche des coordonnées communales, sans correction locale d’altitude.
- 120 heures de prévision, du +1 h au +120 h du calcul sélectionné.
- Après +78 h : interpolation linéaire de la température, des composantes du vent, des nuages et du cumul de précipitations. La pluie par heure correspond alors à une répartition du cumul sur 3 h, pas à un nouveau calcul horaire.
- Les rafales sont des maxima sur la période native indiquée (`gust_period_hours`), sans interpolation trompeuse du maximum. La première heure dépend aussi du pas de cumul natif.
- Les métadonnées distinguent heure de calcul, heure de publication et heures de validité. Les horaires affichés sont ceux de Paris.
- Les nuages sont affichés en %, sans inventer un code de temps sensible à partir de la nébulosité.

La source officielle reste DWD, y compris pour un usage commercial : consulter les [conditions de réutilisation DWD](https://www.dwd.de/EN/service/copyright/copyright_node.html). Attribution DWD conservée dans le module. Catalogue des communes : API administrative française, source indiquée dans `config/communes-france.json`.

## Structure

- `.github/workflows/update-icon-eu.yml` : lancement manuel et automatique, tests, publication, ZIP.
- `scripts/update_icon_eu.py` : lecture des GRIB DWD, contrôle du calcul et de la grille, extraction et conversions.
- `tests/test_pipeline.py` : unités, conservation des précipitations, périodes des rafales, sélection des runs et géographie.
- `wordpress/icon-eu-7-km/` : extension WordPress.
- `app/` : interface React alternative utilisant la même branche `data`.

La branche `data` contient `index.json`, `communes.json` et `departements/XX.json`.

## Développement facultatif

Le lancement sur ordinateur n’est pas nécessaire pour utiliser le ZIP WordPress ou GitHub Actions.

```sh
python -m pip install -r requirements.txt
python -m unittest discover -s tests -p 'test_*.py' -v
python scripts/update_icon_eu.py
```

Interface React : Node.js 22.13+, `pnpm install`, `pnpm dev`, puis ouvrir l’adresse locale indiquée. Compilation : `pnpm build`.
