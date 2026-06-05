from collections import defaultdict
from typing import Any, Dict, Iterable


def _orbit_for_altitude(alt_km: float) -> str:
    if alt_km < 2000:
        return "LEO"
    if alt_km < 35000:
        return "MEO"
    if alt_km < 36500:
        return "GEO"
    return "HEO"


def compute_orbital_heatmap(
    satellites: Iterable[Dict[str, Any]],
    lat_step: int = 15,
    lon_step: int = 30,
    alt_step_km: int = 500,
) -> Dict[str, Any]:
    bins: dict[tuple[int, int, int, str], Dict[str, Any]] = {}
    max_density = 0

    for sat in satellites:
        lat = sat.get("latitude", sat.get("lat"))
        lon = sat.get("longitude", sat.get("lon"))
        alt = sat.get("altitude_km", sat.get("alt_km"))
        if lat is None or lon is None or alt is None:
            continue

        lat = float(lat)
        lon = float(lon)
        alt = max(0.0, float(alt))
        orbit = sat.get("orbit") or _orbit_for_altitude(alt)
        lat_bin = int((lat + 90.0) // lat_step) * lat_step - 90
        lon_bin = int((lon + 180.0) // lon_step) * lon_step - 180
        alt_bin = int(alt // alt_step_km) * alt_step_km
        key = (lat_bin, lon_bin, alt_bin, orbit)

        if key not in bins:
            bins[key] = {
                "lat": lat_bin + lat_step / 2,
                "lon": lon_bin + lon_step / 2,
                "altitude_band_km": [alt_bin, alt_bin + alt_step_km],
                "orbit": orbit,
                "density": 0,
                "satellites": [],
            }
        bins[key]["density"] += 1
        if len(bins[key]["satellites"]) < 8:
            bins[key]["satellites"].append(sat.get("name"))
        max_density = max(max_density, bins[key]["density"])

    cells = list(bins.values())
    for cell in cells:
        cell["risk_score"] = round(cell["density"] / max_density, 3) if max_density else 0.0

    orbit_counts = defaultdict(int)
    for cell in cells:
        orbit_counts[cell["orbit"]] += cell["density"]

    return {
        "cells": sorted(cells, key=lambda c: c["density"], reverse=True)[:300],
        "max_density": max_density,
        "orbit_counts": dict(orbit_counts),
    }
