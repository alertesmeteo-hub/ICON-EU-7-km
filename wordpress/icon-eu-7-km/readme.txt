=== ICON-EU 7 km — Alertes-météo ===
Version: 3.3.0
Requires PHP: 7.4

Installer le ZIP dans Extensions > Ajouter > Téléverser, puis activer.
Dans Avada, ajouter un bloc texte ou code avec : [icon_eu_meteo]
Autre commune : [icon_eu_meteo code="66136"]
Les données viennent de la branche data du dépôt alertesmeteo-hub/ICON-EU-7-km.
Lancer Actions > Mise à jour ICON-EU 7 km > Run workflow avant la première utilisation.
La mise à jour automatique est vérifiée toutes les heures. Aucun secret météo nécessaire.

Version 3.0.0 : cartes fixes France/Europe et zoom interactif pour la température
à 2 m, les précipitations totales, le vent à 10 m, les rafales et la nébulosité,
aux échéances H+24, H+48, H+72, H+96 et H+120.

Version 3.1.0 : interface harmonisée avec les autres modules Alertes-Météo.
Version 3.1.1 : vent et rafales affichés par pas de 5 km/h.

Version 3.3.0 : cartes en plages vectorielles, zoom limité à la zone géographique,
titre et légende fixes. Logo rouge sur noir, non cliquable. Sonde sur tous les
points régionaux sans décimation. Les plages sont interpolées graphiquement :
le zoom ne change pas la résolution météorologique de 7 km.
Nécessite une publication data 3.3.0. Sans SVG, conserve une carte fixe.
