import math
from typing import Any, Dict, Iterable, List


def _pos_tuple(sat: Dict[str, Any]) -> tuple[float, float, float] | None:
    lat = sat.get("latitude", sat.get("lat"))
    lon = sat.get("longitude", sat.get("lon"))
    alt = sat.get("altitude_km", sat.get("alt_km"))
    if lat is None or lon is None or alt is None:
        return None
    return float(lat), float(lon), float(alt)


def _simple_distance(a: tuple[float, float, float], b: tuple[float, float, float]) -> float:
    lat_scale = 111.0
    lon_scale = 111.0 * math.cos(math.radians((a[0] + b[0]) / 2.0))
    dx = (a[1] - b[1]) * lon_scale
    dy = (a[0] - b[0]) * lat_scale
    dz = a[2] - b[2]
    return math.sqrt(dx * dx + dy * dy + dz * dz)


def simulate_kessler_risk(
    satellites: Iterable[Dict[str, Any]],
    conjunctions: Iterable[Dict[str, Any]],
    max_events: int = 5,
    cloud_radius_km: float = 250.0,
) -> Dict[str, Any]:
    sats = list(satellites)
    by_name = {sat.get("name"): sat for sat in sats if sat.get("name")}
    events = sorted(
        list(conjunctions),
        key=lambda c: c.get("distance_km", 999999.0),
    )[:max_events]

    clouds = []
    chain_total = 0.0
    for idx, event in enumerate(events):
        name1 = event.get("sat1") or event.get("obj1")
        name2 = event.get("sat2") or event.get("obj2")
        sat1 = by_name.get(name1)
        sat2 = by_name.get(name2)
        p1 = _pos_tuple(sat1 or {})
        p2 = _pos_tuple(sat2 or {})
        if not p1 or not p2:
            continue

        miss_distance = max(0.1, float(event.get("distance_km") or 999999.0))
        primary_probability = min(0.85, 0.015 * (50.0 / miss_distance) ** 1.35)
        center = ((p1[0] + p2[0]) / 2.0, (p1[1] + p2[1]) / 2.0, (p1[2] + p2[2]) / 2.0)
        debris_count = int(80 + max(0, 500.0 - miss_distance) * 1.8)

        affected = []
        for sat in sats:
            name = sat.get("name")
            if name in (name1, name2):
                continue
            pos = _pos_tuple(sat)
            if not pos:
                continue
            distance = _simple_distance(center, pos)
            if distance <= cloud_radius_km:
                chain_probability = primary_probability * max(0.0, 1.0 - distance / cloud_radius_km)
                if chain_probability > 0.0005:
                    affected.append({
                        "satellite": name,
                        "distance_to_cloud_km": round(distance, 2),
                        "chain_probability": round(chain_probability, 5),
                    })

        affected = sorted(affected, key=lambda x: x["chain_probability"], reverse=True)[:12]
        chain_total += sum(a["chain_probability"] for a in affected)
        clouds.append({
            "id": f"cloud_{idx + 1}",
            "source": [name1, name2],
            "center": {
                "lat": round(center[0], 4),
                "lon": round(center[1], 4),
                "altitude_km": round(center[2], 2),
            },
            "radius_km": cloud_radius_km,
            "debris_count": debris_count,
            "primary_probability": round(primary_probability, 5),
            "affected_satellites": affected,
        })

    return {
        "clouds": clouds,
        "event_count": len(clouds),
        "chain_probability_sum": round(chain_total, 5),
    }
