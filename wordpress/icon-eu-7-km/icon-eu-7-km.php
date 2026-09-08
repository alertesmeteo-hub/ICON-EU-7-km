<?php
/**
 * Plugin Name: ICON-EU 7 km — Alertes-météo
 * Description: Prévisions officielles DWD préparées par GitHub Actions. Shortcode [icon_eu_meteo].
 * Version: 2.0.0
 * Requires PHP: 7.4
 * Author: Alertes-météo
 */
if (!defined('ABSPATH')) { exit; }
add_shortcode('icon_eu_meteo', function ($atts) {
    $atts = shortcode_atts(array('code' => '75056'), $atts, 'icon_eu_meteo');
    $code = preg_match('/^[0-9A-Z]{5}$/', $atts['code']) ? $atts['code'] : '75056';
    wp_enqueue_style('icon-eu-7-km', plugins_url('assets/icon-eu.css', __FILE__), array(), '2.0.0');
    wp_enqueue_script('icon-eu-7-km', plugins_url('assets/icon-eu.js', __FILE__), array(), '2.0.0', true);
    $id = wp_unique_id('icon-eu-');
    ob_start(); ?>
    <section class="icon-eu-widget" data-code="<?php echo esc_attr($code); ?>" data-source="https://raw.githubusercontent.com/alertesmeteo-hub/ICON-EU-7-km/data/">
      <header><span>ALERTES-MÉTÉO · DWD</span><h2>Prévisions ICON-EU · 7 km</h2></header>
      <label for="<?php echo esc_attr($id); ?>">Commune ou code postal</label>
      <input id="<?php echo esc_attr($id); ?>" class="icon-eu-search" type="search" placeholder="Paris, Lyon, 66000…" autocomplete="off">
      <ul class="icon-eu-results"></ul>
      <div class="icon-eu-toolbar"><h3 class="icon-eu-city"></h3><button type="button" class="icon-eu-refresh">Actualiser</button></div>
      <p class="icon-eu-meta"></p><p class="icon-eu-status" role="status">Chargement des prévisions…</p>
      <div class="icon-eu-days" aria-label="Choisir un jour"></div><div class="icon-eu-table" tabindex="0" aria-label="Prévisions horaires"></div>
      <p class="icon-eu-note">Source : <a href="https://opendata.dwd.de/weather/nwp/icon-eu/" target="_blank" rel="noopener noreferrer">DWD Open Data — ICON-EU</a>. Point de grille le plus proche de la commune, sans correction locale d’altitude. Heures de Paris. Après +78 h, température, vent et nuages sont interpolés ; les précipitations sont réparties sur trois heures et les rafales restent des maxima sur leur période indiquée. Ce sont des prévisions, pas des observations.</p>
    </section>
    <?php return ob_get_clean();
});
