#!/usr/bin/env python3
"""DWD ICON-EU regular 0.0625-degree GRIB -> department JSON, no API key."""
import argparse
import bz2
import concurrent.futures
import json
import math
import re
import tempfile
import time
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

import numpy as np

BASE = 'https://opendata.dwd.de/weather/nwp/icon-eu/grib/'
VARIABLES = ('t_2m', 'tot_prec', 'u_10m', 'v_10m', 'vmax_10m', 'clct')
STEPS = list(range(79)) + list(range(81, 121, 3))
COLUMNS = ['temperature_2m', 'precipitation', 'wind_speed_10m', 'wind_gusts_10m', 'cloud_cover']
UNITS = {'temperature_2m': '°C', 'precipitation': 'mm', 'wind_speed_10m': 'km/h', 'wind_gusts_10m': 'km/h', 'cloud_cover': '%'}

def download(url):
    for attempt in range(4):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent':'AlertesMeteo-ICON-EU/2.0'}), timeout=90) as r:
                return r.read()
        except Exception:
            if attempt == 3: raise
            time.sleep(2 ** (attempt + 1))

def available(hour, variable):
    url = f'{BASE}{hour:02d}/{variable}/'
    html = download(url).decode()
    pattern = r'href="(icon-eu_europe_regular-lat-lon_single-level_(\d{10})_(\d{3})_[^"]+\.grib2\.bz2)"'
    return {(run, int(step)): url + name for name, run, step in re.findall(pattern, html)}

def select_run(listings):
    runs = sorted({run for run, _ in listings['t_2m']}, reverse=True)
    for run in runs:
        if all(all((run, step) in listings[v] for step in STEPS) for v in VARIABLES):
            return run
    raise RuntimeError('Aucun calcul complet à +120 h : dernière publication conservée.')

def grid_indices(meta, latitudes, longitudes):
    if meta['gridType'] != 'regular_ll' or meta['jPointsAreConsecutive'] or meta['alternativeRowScanning']:
        raise ValueError('Unsupported ICON-EU grid layout')
    dx = meta['iDirectionIncrementInDegrees'] * (-1 if meta['iScansNegatively'] else 1)
    dy = meta['jDirectionIncrementInDegrees'] * (1 if meta['jScansPositively'] else -1)
    delta = (longitudes - meta['longitudeOfFirstGridPointInDegrees'] + 180) % 360 - 180
    x = np.rint(delta / dx).astype(int)
    y = np.rint((latitudes - meta['latitudeOfFirstGridPointInDegrees']) / dy).astype(int)
    if np.any((x < 0) | (x >= meta['Ni']) | (y < 0) | (y >= meta['Nj'])):
        raise ValueError('Commune outside ICON-EU grid')
    return y * meta['Ni'] + x

def read_field(url, run, step, variable, communes):
    from eccodes import codes_grib_new_from_file, codes_get, codes_get_double_elements, codes_release
    payload = bz2.decompress(download(url))
    with tempfile.TemporaryFile() as f:
        f.write(payload); f.seek(0)
        handle = codes_grib_new_from_file(f)
        if handle is None: raise ValueError('Empty GRIB')
        try:
            actual_run = f"{int(codes_get(handle,'dataDate')):08d}{int(codes_get(handle,'dataTime'))//100:02d}"
            if actual_run != run or int(codes_get(handle, 'endStep')) != step:
                raise ValueError('Mixed model runs or lead times')
            keys = ('gridType', 'Ni', 'Nj', 'jPointsAreConsecutive', 'alternativeRowScanning', 'iDirectionIncrementInDegrees', 'jDirectionIncrementInDegrees', 'iScansNegatively', 'jScansPositively', 'longitudeOfFirstGridPointInDegrees', 'latitudeOfFirstGridPointInDegrees')
            meta = {k: codes_get(handle, k) for k in keys}
            if abs(meta['iDirectionIncrementInDegrees'] - .0625) > .00001: raise ValueError('Unexpected ICON-EU resolution')
            indices = grid_indices(meta, np.array([c[5] for c in communes]), np.array([c[6] for c in communes]))
            values = np.asarray(codes_get_double_elements(handle, 'values', indices.tolist()))
            if not np.all(np.isfinite(values)) or np.any(np.abs(values) > 1e10): raise ValueError('Missing GRIB values')
            units = str(codes_get(handle, 'units'))
            expected = {'t_2m': ('K',), 'tot_prec': ('kg m**-2', 'kg m-2', 'mm'), 'u_10m': ('m s**-1', 'm s-1'), 'v_10m': ('m s**-1', 'm s-1'), 'vmax_10m': ('m s**-1', 'm s-1'), 'clct': ('%',)}
            if units not in expected[variable]: raise ValueError(f'Unexpected units for {variable}: {units}')
            start = int(codes_get(handle, 'startStep'))
            if variable == 'tot_prec' and start != 0: raise ValueError('Precipitation must accumulate from model start')
            return values, start
        finally: codes_release(handle)

def to_hourly(raw, starts, steps=STEPS):
    hours = np.arange(121)
    expanded = {v: np.stack([np.interp(hours, steps, row) for row in a.T], axis=1) for v,a in raw.items() if v != 'vmax_10m'}
    # Gust is a period maximum: preserve that period value, never call it an hourly maximum after +78 h.
    gust = np.empty((121, raw['vmax_10m'].shape[1])); periods = np.empty(121, dtype=int)
    previous = -1
    for i, end in enumerate(steps):
        gust[previous+1:end+1] = raw['vmax_10m'][i]
        periods[previous+1:end+1] = max(1, end - starts[i])
        previous = end
    cumulative = expanded['tot_prec']
    if np.min(np.diff(cumulative, axis=0)) < -.05: raise ValueError('Precipitation accumulation decreased')
    rain = np.maximum(0, np.diff(cumulative, axis=0))
    wind = np.hypot(expanded['u_10m'], expanded['v_10m']) * 3.6
    result = np.stack([expanded['t_2m'][1:] - 273.15, rain, wind[1:], gust[1:] * 3.6, expanded['clct'][1:]], axis=2)
    if not np.all(np.isfinite(result)): raise ValueError('Non-finite output')
    return np.round(result, 1), periods[1:].tolist()

def generate(catalog, output, repository, force=False):
    communes = json.loads(Path(catalog).read_text(encoding='utf-8-sig'))['communes']
    listings = {v:{} for v in VARIABLES}
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        jobs = {pool.submit(available,h,v): v for h in (0,6,12,18) for v in VARIABLES}
        for future in concurrent.futures.as_completed(jobs): listings[jobs[future]].update(future.result())
    run = select_run(listings)
    run_date = datetime.strptime(run, '%Y%m%d%H').replace(tzinfo=timezone.utc)
    if datetime.now(timezone.utc) - run_date > timedelta(hours=30): raise ValueError('Latest complete model run is stale')
    current_url = f'https://raw.githubusercontent.com/{repository}/data/index.json'
    if not force:
        try: current = json.loads(download(current_url))
        except urllib.error.HTTPError as e:
            if e.code != 404: raise
            current = {}
        if current.get('model_run') == run_date.isoformat():
            print('Calcul déjà publié : aucune modification.', flush=True); return
    print(f'ICON-EU {run}: {len(communes)} communes, {len(STEPS)} échéances natives, {len(VARIABLES)} paramètres', flush=True)
    raw = {v: np.empty((len(STEPS), len(communes))) for v in VARIABLES}; starts = [0] * len(STEPS)
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        jobs = {pool.submit(read_field,listings[v][(run,s)],run,s,v,communes):(v,i) for v in VARIABLES for i,s in enumerate(STEPS)}
        for count, future in enumerate(concurrent.futures.as_completed(jobs),1):
            v,i = jobs[future]; field,start = future.result(); raw[v][i] = field
            if v == 'vmax_10m': starts[i] = start
            if count % 30 == 0: print(f'{count}/{len(jobs)} fichiers validés', flush=True)
    hourly, gust_periods = to_hourly(raw, starts)
    output = Path(output); output.mkdir(parents=True, exist_ok=True)
    times = [int((run_date + timedelta(hours=h)).timestamp()) for h in range(1,121)]
    departments = sorted({c[2] for c in communes})
    if len(departments) != 96: raise ValueError('Expected 96 metropolitan departments')
    metadata = {'schema_version':2, 'status':'ok', 'model':'ICON-EU', 'resolution_km':7, 'model_run':run_date.isoformat(), 'generated_at':datetime.now(timezone.utc).isoformat(), 'source':'DWD Open Data', 'source_url':BASE, 'timezone':'Europe/Paris', 'time':times, 'columns':COLUMNS, 'units':UNITS, 'gust_period_hours':gust_periods, 'interpolated_after_hour':78, 'coverage':{'communes':len(communes),'departments':len(departments)}, 'forecast_hours':120}
    (output/'departements').mkdir(exist_ok=True)
    for department in departments:
        indices = [i for i,c in enumerate(communes) if c[2] == department]
        payload = {**metadata, 'department':department, 'communes':{communes[i][0]:{'name':communes[i][1], 'latitude':communes[i][5], 'longitude':communes[i][6], 'values':hourly[:,i,:].tolist()} for i in indices}}
        (output/'departements'/f'{department}.json').write_text(json.dumps(payload,ensure_ascii=False,separators=(',',':'),allow_nan=False),encoding='utf-8')
    compact = {'model_run': metadata['model_run'], 'columns':['code','name','department','postal_codes','latitude','longitude'], 'communes':[[c[0],c[1],c[2],c[3],c[5],c[6]] for c in communes]}
    (output/'communes.json').write_text(json.dumps(compact,ensure_ascii=False,separators=(',',':')),encoding='utf-8')
    (output/'index.json').write_text(json.dumps(metadata,ensure_ascii=False,indent=2),encoding='utf-8')
    print(f'Publication complète : {len(communes)} communes, 96 départements.', flush=True)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(); parser.add_argument('--catalog',default='config/communes-france.json'); parser.add_argument('--output-dir',default='build/national'); parser.add_argument('--repository',default='alertesmeteo-hub/ICON-EU-7-km'); parser.add_argument('--force',action='store_true')
    args=parser.parse_args(); generate(args.catalog,args.output_dir,args.repository,args.force)
