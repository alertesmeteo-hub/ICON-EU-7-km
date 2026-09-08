export type Place = {id: string; name: string; latitude: number; longitude: number; department: string; admin1?: string; postalCodes?: string[]};
export type Forecast = {hourly: Record<string, (number | null)[]> & {time: number[]}; timezone: string; model_run: string; generated_at: string; gust_period_hours: number[]};
const SOURCE = 'https://raw.githubusercontent.com/alertesmeteo-hub/ICON-EU-7-km/data/';
type Catalog = {communes: [string, string, string, string[], number, number][]};
type Department = {schema_version: number; model: string; time: number[]; timezone: string; model_run: string; generated_at: string; columns: string[]; gust_period_hours: number[]; communes: Record<string, {values: (number | null)[][]}>};
async function json<T>(file: string, signal: AbortSignal): Promise<T> {
  const r = await fetch(SOURCE + file, {signal: AbortSignal.any([signal, AbortSignal.timeout(30000)]), cache: 'no-cache'});
  if (!r.ok) throw Error('Prévisions indisponibles. Attendez la fin du run GitHub, puis réessayez.');
  return r.json() as Promise<T>;
}
let catalog: Place[] | null = null;
export async function searchPlaces(query: string, signal: AbortSignal): Promise<Place[]> {
  if (!catalog) {
    const data = await json<Catalog>('communes.json', signal);
    if (!Array.isArray(data.communes)) throw Error('Catalogue indisponible.');
    catalog = data.communes.map(c => ({id: c[0], name: c[1], department: c[2], admin1: 'Département ' + c[2], postalCodes: c[3], latitude: c[4], longitude: c[5]}));
  }
  const norm = (s: string) => s.normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLowerCase();
  const q = norm(query.trim());
  return catalog.filter(c => norm(c.name).includes(q) || c.id === q || c.postalCodes?.some(p => p.startsWith(q))).slice(0, 12);
}
export async function getForecast(place: Place, signal: AbortSignal): Promise<Forecast> {
  const data = await json<Department>('departements/' + encodeURIComponent(place.department) + '.json', signal);
  const commune = data.communes?.[place.id];
  if (data.model !== 'ICON-EU' || data.schema_version !== 2 || !commune || commune.values.length !== data.time.length) throw Error('Prévisions ICON-EU incomplètes.');
  const hourly: Forecast['hourly'] = {time: data.time};
  data.columns.forEach((field, index) => {hourly[field] = commune.values.map(row => row[index]);});
  return {hourly, timezone: data.timezone, model_run: data.model_run, generated_at: data.generated_at, gust_period_hours: data.gust_period_hours};
}
