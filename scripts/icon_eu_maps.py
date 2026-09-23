"""Production des cartes fixes France/Europe à partir des GRIB ICON-EU DWD."""
from __future__ import annotations

import bz2
import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np


REGIONS = {
    "france": (-6.0, 10.5, 41.0, 52.0),
    "europe": (-25.0, 45.0, 30.0, 72.0),
}
MAP_STEPS = (24, 48, 72, 96, 120)
PRODUCTS = {
    "temperature": {"label": "Température à 2 m", "unit": "°C", "variable": "t_2m",
                    "levels": np.arange(-30, 43, 3), "cmap": "turbo"},
    "precipitation": {"label": "Précipitations totales", "unit": "mm", "variable": "tot_prec",
                      "levels": np.array([0.1, 1, 2, 5, 10, 15, 20, 30, 40, 50, 70, 100, 150, 200]), "cmap": "turbo"},
    "rafales": {"label": "Rafales maximales à l’échéance", "unit": "km/h", "variable": "vmax_10m",
                "levels": np.arange(0, 181, 10), "cmap": "turbo"},
    "nuages": {"label": "Couverture nuageuse totale", "unit": "%", "variable": "clct",
               "levels": np.arange(0, 110, 10), "cmap": "Blues"},
    "vent": {"label": "Vent moyen à 10 m", "unit": "km/h", "variable": ("u_10m", "v_10m"),
             "levels": np.arange(0, 121, 10), "cmap": "viridis"},
}


def _decode(payload: bytes, run: str, step: int):
    from eccodes import codes_get, codes_get_values, codes_new_from_message, codes_release
    handle = codes_new_from_message(bz2.decompress(payload))
    if handle is None:
        raise ValueError("GRIB ICON-EU vide")
    try:
        actual_run = f"{int(codes_get(handle, 'dataDate')):08d}{int(codes_get(handle, 'dataTime')) // 100:02d}"
        if actual_run != run or int(codes_get(handle, "endStep")) != step:
            raise ValueError("Calcul ou échéance ICON-EU incohérent")
        ni, nj = int(codes_get(handle, "Ni")), int(codes_get(handle, "Nj"))
        lon0 = float(codes_get(handle, "longitudeOfFirstGridPointInDegrees"))
        lat0 = float(codes_get(handle, "latitudeOfFirstGridPointInDegrees"))
        dx = float(codes_get(handle, "iDirectionIncrementInDegrees"))
        dy = float(codes_get(handle, "jDirectionIncrementInDegrees"))
        if int(codes_get(handle, "iScansNegatively")):
            dx = -dx
        if not int(codes_get(handle, "jScansPositively")):
            dy = -dy
        values = np.asarray(codes_get_values(handle), dtype=float).reshape(nj, ni)
        lon = ((lon0 + np.arange(ni) * dx + 180) % 360) - 180
        lat = lat0 + np.arange(nj) * dy
        order = np.argsort(lon)
        return lon[order], lat, values[:, order]
    finally:
        codes_release(handle)


def _draw_boundaries(ax, config_dir: Path):
    import shapefile
    for name, width in (("ne_50m_coastline", .55), ("ne_50m_admin_0_boundary_lines_land", .4)):
        reader = shapefile.Reader(str(config_dir / "natural-earth" / name))
        for shape in reader.shapes():
            points = np.asarray(shape.points)
            if not len(points):
                continue
            parts = list(shape.parts) + [len(points)]
            for start, end in zip(parts, parts[1:]):
                ax.plot(points[start:end, 0], points[start:end, 1], color="#4d5558", linewidth=width, zorder=3)


def _render(lon, lat, values, product, region, run, step, output, config_dir):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.colors import BoundaryNorm
    spec = PRODUCTS[product]
    west, east, south, north = REGIONS[region]
    fig, ax = plt.subplots(figsize=(11.5, 8 if region == "france" else 7), dpi=140)
    norm = BoundaryNorm(spec["levels"], plt.get_cmap(spec["cmap"]).N, clip=True)
    mesh = ax.pcolormesh(lon, lat, values, cmap=spec["cmap"], norm=norm, shading="auto", rasterized=True)
    _draw_boundaries(ax, config_dir)
    ax.set(xlim=(west, east), ylim=(south, north), xlabel="", ylabel="")
    ax.set_xticks([]); ax.set_yticks([])
    run_dt = datetime.strptime(run, "%Y%m%d%H").replace(tzinfo=timezone.utc)
    ax.set_title(f"ICON-EU 7 km — {spec['label']} ({spec['unit']})\nRun {run_dt:%d/%m/%Y %H} UTC · H+{step}", fontsize=12, fontweight="bold")
    bar = fig.colorbar(mesh, ax=ax, orientation="vertical", pad=.015, fraction=.035)
    bar.set_label(spec["unit"], fontweight="bold")
    ax.text(.5, .018, "www.alertes-meteo.com", transform=ax.transAxes, ha="center", va="bottom",
            fontsize=8, color="white", fontweight="bold",
            bbox={"facecolor": "#18353e", "alpha": .88, "edgecolor": "none", "pad": 4})
    output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output, bbox_inches="tight", facecolor="white")
    plt.close(fig)


def generate_maps(listings, run, output_dir, download, config_dir):
    output_dir, config_dir = Path(output_dir), Path(config_dir)
    manifests = {name: [] for name in PRODUCTS}
    cache = {}
    for step in MAP_STEPS:
        for product, spec in PRODUCTS.items():
            variables = spec["variable"] if isinstance(spec["variable"], tuple) else (spec["variable"],)
            fields = []
            for variable in variables:
                key = (variable, step)
                if key not in cache:
                    cache[key] = _decode(download(listings[variable][(run, step)]), run, step)
                fields.append(cache[key])
            lon, lat = fields[0][0], fields[0][1]
            if product == "vent":
                values = np.hypot(fields[0][2], fields[1][2]) * 3.6
            else:
                values = fields[0][2]
                if product == "temperature": values = values - 273.15
                if product == "rafales": values = values * 3.6
            for region in REGIONS:
                relative = f"maps/{region}/{product}-{step:03d}h.png"
                _render(lon, lat, values, product, region, run, step, output_dir / relative, config_dir)
                manifests[product].append({"region": region, "lead_hour": step, "image": relative})
    payload = {"model": "ICON-EU", "pipeline_version": "3.1.0", "resolution_km": 7, "run": run, "steps": list(MAP_STEPS),
               "products": {key: {"label": value["label"], "unit": value["unit"], "maps": manifests[key]}
                            for key, value in PRODUCTS.items()}}
    (output_dir / "maps" / "manifest.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return payload
