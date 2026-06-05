import math
from dataclasses import dataclass
from typing import Any, Dict, Iterable, List


EARTH_RADIUS_KM = 6378.137


@dataclass(frozen=True)
class GroundStation:
    id: str
    name: str
    latitude: float
    longitude: float
    altitude_km: float
    min_elevation_deg: float = 10.0


DEFAULT_GROUND_STATIONS = [
    GroundStation("white_sands", "White Sands", 32.5007, -106.6086, 1.2),
    GroundStation("goldstone", "Goldstone DSN", 35.4267, -116.89, 1.0),
    GroundStation("madrid", "Madrid DSN", 40.4314, -4.2481, 0.8),
    GroundStation("canberra", "Canberra DSN", -35.3985, 148.9819, 0.7),
    GroundStation("sriharikota", "Sriharikota", 13.7199, 80.2304, 0.0),
]


def _lla_to_ecef(lat_deg: float, lon_deg: float, alt_km: float) -> tuple[float, float, float]:
    lat = math.radians(lat_deg)
    lon = math.radians(lon_deg)
    r = EARTH_RADIUS_KM + alt_km
    return (
        r * math.cos(lat) * math.cos(lon),
        r * math.cos(lat) * math.sin(lon),
        r * math.sin(lat),
    )


def _elevation_angle_deg(
    sat_lat: float,
    sat_lon: float,
    sat_alt_km: float,
    station: GroundStation,
) -> float:
    sx, sy, sz = _lla_to_ecef(sat_lat, sat_lon, sat_alt_km)
    gx, gy, gz = _lla_to_ecef(station.latitude, station.longitude, station.altitude_km)
    rx, ry, rz = sx - gx, sy - gy, sz - gz

    lat = math.radians(station.latitude)
    lon = math.radians(station.longitude)
    up = (math.cos(lat) * math.cos(lon), math.cos(lat) * math.sin(lon), math.sin(lat))
    rng = math.sqrt(rx * rx + ry * ry + rz * rz)
    if rng <= 0:
        return -90.0

    dot_up = rx * up[0] + ry * up[1] + rz * up[2]
    return math.degrees(math.asin(max(-1.0, min(1.0, dot_up / rng))))


def _satellite_key(sat: Dict[str, Any], key: str, fallback: str) -> Any:
    return sat.get(key) if sat.get(key) is not None else sat.get(fallback)


def estimate_visibility_duration_seconds(elevation_deg: float, altitude_km: float) -> int:
    """Cheap pass-duration approximation for live UI display.

    Higher elevation means the object is closer to pass center. LEO passes are
    short, while MEO/GEO visibility windows are longer.
    """
    if elevation_deg <= 0:
        return 0
    if altitude_km < 2000:
        max_duration = 11 * 60
    elif altitude_km < 35000:
        max_duration = 45 * 60
    else:
        max_duration = 6 * 60 * 60
    return int(max_duration * min(1.0, elevation_deg / 85.0))


def compute_ground_visibility(
    satellites: Iterable[Dict[str, Any]],
    stations: List[GroundStation] | None = None,
    max_satellites: int = 2000,
) -> Dict[str, Any]:
    stations = stations or DEFAULT_GROUND_STATIONS
    station_payload = [
        {
            "id": s.id,
            "name": s.name,
            "latitude": s.latitude,
            "longitude": s.longitude,
            "altitude_km": s.altitude_km,
            "min_elevation_deg": s.min_elevation_deg,
        }
        for s in stations
    ]

    visible = []
    for sat in list(satellites)[:max_satellites]:
        lat = _satellite_key(sat, "latitude", "lat")
        lon = _satellite_key(sat, "longitude", "lon")
        alt = _satellite_key(sat, "altitude_km", "alt_km")
        if lat is None or lon is None or alt is None:
            continue

        best = None
        for station in stations:
            elevation = _elevation_angle_deg(float(lat), float(lon), float(alt), station)
            if elevation >= station.min_elevation_deg:
                duration = estimate_visibility_duration_seconds(elevation, float(alt))
                candidate = {
                    "satellite": sat.get("name"),
                    "station_id": station.id,
                    "station_name": station.name,
                    "elevation_deg": round(elevation, 2),
                    "duration_seconds": duration,
                }
                if best is None or candidate["elevation_deg"] > best["elevation_deg"]:
                    best = candidate
        if best:
            visible.append(best)

    return {
        "stations": station_payload,
        "visible": visible,
        "visible_count": len(visible),
    }
