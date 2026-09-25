<?php
/**
 * Plugin Name: ICON-EU 7 km — Alertes-météo
 * Description: Prévisions officielles DWD préparées par GitHub Actions. Shortcode [icon_eu_meteo].
 * Version: 3.3.0
 * Requires PHP: 7.4
 * Author: Alertes-météo
 */
if (!defined('ABSPATH')) { exit; }
add_shortcode('icon_eu_meteo', function ($atts) {
    $atts = shortcode_atts(array('code' => '75056'), $atts, 'icon_eu_meteo');
    $code = preg_match('/^[0-9A-Z]{5}$/', $atts['code']) ? $atts['code'] : '75056';
    wp_enqueue_style('icon-eu-7-km', plugins_url('assets/icon-eu.css', __FILE__), array(), '3.3.0');
    wp_enqueue_script('iconeu-vector', plugins_url('assets/icon-vector-zoom.js', __FILE__), array(), '3.3.0', true);
    wp_enqueue_script('icon-eu-7-km', plugins_url('assets/icon-eu.js', __FILE__), array('iconeu-vector'), '3.3.0', true);
    $id = wp_unique_id('icon-eu-');
    ob_start(); ?>
    <section class="icon-eu-widget" data-code="<?php echo esc_attr($code); ?>" data-source="https://raw.githubusercontent.com/alertesmeteo-hub/ICON-EU-7-km/data/">
      <header><div><span>MODÈLE RÉGIONAL · EUROPE</span><h2>Prévisions ICON-EU — France et Europe</h2><p>Données officielles DWD · échéances jusqu’à H+120</p></div><strong>ICON‑EU <b>7 km</b></strong></header>
      <div class="icon-eu-search-zone"><label for="<?php echo esc_attr($id); ?>">Choisissez votre commune</label>
        <input id="<?php echo esc_attr($id); ?>" class="icon-eu-search" type="search" placeholder="Paris, Lyon, 66000…" autocomplete="off">
        <ul class="icon-eu-results"></ul>
      </div>
      <nav class="icon-eu-tabs" aria-label="Type de prévision ICON-EU">
        <button type="button" data-icon-view="fixed" aria-pressed="true">Cartes fixes Europe/France</button>
        <button type="button" data-icon-view="france">France interactive</button>
        <button type="button" data-icon-view="europe">Europe interactive</button>
        <span>Tableau :</span><button type="button" data-icon-view="table">🌤️ Général</button>
      </nav>
      <section class="icon-eu-map-panel">
        <div class="icon-eu-map-tools">
          <div class="icon-eu-products" aria-label="Paramètre météo"></div>
          <div class="icon-eu-regions"><button type="button" data-icon-region="france" aria-pressed="true">France</button><button type="button" data-icon-region="europe">Europe</button></div>
          <div class="icon-eu-leads" aria-label="Échéance"></div>
        </div>
        <p class="icon-eu-map-summary"></p>
        <div class="icon-eu-map-viewer">
          <img class="icon-eu-map-image" alt="Carte ICON-EU 7 km">
          <div class="icon-eu-map-probe" hidden><strong></strong><span></span></div>
          <div class="icon-eu-zoom"><button type="button" data-icon-zoom="in">+</button><button type="button" data-icon-zoom="out">−</button><button type="button" data-icon-zoom="reset">⌂</button></div>
          <p class="icon-eu-map-status" role="status">Chargement des cartes…</p>
        </div>
      </section>
      <section class="icon-eu-table-panel" hidden>
        <div class="icon-eu-toolbar"><h3 class="icon-eu-city"></h3><button type="button" class="icon-eu-refresh">Actualiser</button></div>
        <p class="icon-eu-meta"></p><p class="icon-eu-status" role="status">Chargement des prévisions…</p>
        <div class="icon-eu-days" aria-label="Choisir un jour"></div><div class="icon-eu-table" tabindex="0" aria-label="Prévisions horaires"></div>
      </section>
      <p class="icon-eu-note">Source : <a href="https://opendata.dwd.de/weather/nwp/icon-eu/" target="_blank" rel="noopener noreferrer">DWD Open Data — ICON-EU</a>. Point de grille le plus proche de la commune, sans correction locale d’altitude. Heures de Paris. Après +78 h, température, vent et nuages sont interpolés ; les précipitations sont réparties sur trois heures et les rafales restent des maxima sur leur période indiquée. Ce sont des prévisions, pas des observations.</p>
      <footer class="icon-eu-footer"><span>Données DWD Open Data · ICON‑EU</span><strong>Module ICON‑EU v3.3.0</strong></footer>
    </section>
    <?php return ob_get_clean();
});
