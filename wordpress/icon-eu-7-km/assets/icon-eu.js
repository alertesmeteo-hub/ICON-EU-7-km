(() => {
  'use strict';
  const normalize = s => String(s).normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLowerCase();
  const date = t => new Date(t * 1000).toLocaleDateString('fr-CA', { timeZone: 'Europe/Paris' });
  const format = (value, unit) => value == null ? '—' : Number(value).toLocaleString('fr-FR', { maximumFractionDigits: 1 }) + ' ' + unit;
  const moment = s => new Date(s).toLocaleString('fr-FR', { timeZone: 'Europe/Paris' });
  const fetchJson = async url => {
    const response = await fetch(url, { signal: AbortSignal.timeout(30000), cache: 'no-cache' });
    if (!response.ok) throw Error('Prévisions indisponibles. Vérifiez que le premier run GitHub est terminé, puis réessayez.');
    return response.json();
  };
  function init(root) {
    if (root.dataset.ready) return;
    root.dataset.ready = 'true';
    const el = name => root.querySelector('.icon-eu-' + name);
    const source = root.dataset.source;
    let catalog = [], metadata = null, selected = null, request = 0;
    const clear = () => { el('table').replaceChildren(); el('days').replaceChildren(); el('meta').textContent = ''; };
    async function load(place) {
      selected = place;
      const seq = ++request;
      clear(); el('city').textContent = place[1]; el('status').textContent = 'Chargement…';
      try {
        const data = await fetchJson(source + 'departements/' + encodeURIComponent(place[2]) + '.json');
        if (seq !== request) return;
        const commune = data.communes?.[place[0]];
        if (!commune || data.model !== 'ICON-EU' || data.schema_version !== 2 || !Array.isArray(data.time) || commune.values.length !== data.time.length) throw Error('Prévisions incomplètes pour cette commune.');
        const now = Date.now() / 1000;
        const indices = data.time.map((_, i) => i).filter(i => data.time[i] >= now - 3600);
        if (!indices.length) throw Error('Ces prévisions sont expirées. Une nouvelle publication GitHub est nécessaire.');
        const age = (Date.now() - Date.parse(data.model_run)) / 3600000;
        el('status').textContent = age > 18 ? 'Le dernier calcul disponible date de plus de 18 h. Consultez sa date avant utilisation.' : '';
        el('meta').textContent = 'Calcul du ' + moment(data.model_run) + ' · publication du ' + moment(data.generated_at);
        const days = [...new Set(indices.map(i => date(data.time[i])))];
        function show(day) {
          const table = document.createElement('table');
          const head = document.createElement('thead'), header = document.createElement('tr');
          ['Heure', 'Température', 'Précipitations', 'Vent', 'Rafales', 'Nuages'].forEach(label => { const th = document.createElement('th'); th.scope = 'col'; th.textContent = label; header.append(th); });
          head.append(header); table.append(head);
          const body = document.createElement('tbody');
          indices.filter(i => date(data.time[i]) === day).forEach(i => {
            const v = commune.values[i], tr = document.createElement('tr');
            const cells = [new Date(data.time[i] * 1000).toLocaleTimeString('fr-FR', { timeZone: 'Europe/Paris', hour: '2-digit', minute: '2-digit' }), format(v[0], '°C'), format(v[1], 'mm'), format(v[2], 'km/h'), format(v[3], 'km/h') + ' / ' + data.gust_period_hours[i] + ' h', format(v[4], '%')];
            cells.forEach(value => { const td = document.createElement('td'); td.textContent = value; tr.append(td); }); body.append(tr);
          });
          table.append(body); el('table').replaceChildren(table);
          el('days').querySelectorAll('button').forEach(b => b.setAttribute('aria-pressed', String(b.dataset.day === day)));
        }
        days.forEach(day => { const b = document.createElement('button'); b.type = 'button'; b.dataset.day = day; b.textContent = new Date(day + 'T12:00:00').toLocaleDateString('fr-FR', { weekday: 'short', day: 'numeric', month: 'short' }); b.addEventListener('click', () => show(day)); el('days').append(b); });
        show(days[0]);
      } catch (error) { if (seq === request) { clear(); el('status').textContent = error.message; } }
    }
    async function boot() {
      try {
        [metadata, { communes: catalog }] = await Promise.all([fetchJson(source + 'index.json'), fetchJson(source + 'communes.json')]);
        if (metadata.model !== 'ICON-EU' || !Array.isArray(catalog)) throw Error('Catalogue ICON-EU indisponible.');
        const place = catalog.find(c => c[0] === root.dataset.code) || catalog.find(c => c[0] === '75056');
        if (!place) throw Error('Commune initiale absente du catalogue.');
        await load(place);
      } catch (error) { el('status').textContent = error.message; }
    }
    el('search').addEventListener('input', () => {
      const term = normalize(el('search').value.trim()); el('results').replaceChildren();
      if (term.length < 2) return;
      const matches = catalog.filter(c => normalize(c[1]).includes(term) || c[3].some(p => p.startsWith(term)) || c[0] === term).slice(0, 12);
      matches.forEach(c => { const li = document.createElement('li'), b = document.createElement('button'); b.type = 'button'; b.textContent = c[1] + ' · ' + c[2]; b.addEventListener('click', () => { el('search').value = ''; el('results').replaceChildren(); void load(c); }); li.append(b); el('results').append(li); });
      if (!matches.length) { const li = document.createElement('li'); li.textContent = 'Aucune commune trouvée.'; el('results').append(li); }
    });
    el('refresh').addEventListener('click', () => { if (selected) void load(selected); else void boot(); });
    void boot();
  }
  function start() { document.querySelectorAll('.icon-eu-widget').forEach(init); }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', start); else start();
})();

