import json
import os
import time
import urllib.request
from datetime import datetime, timezone
from typing import Any, Dict, List


LAUNCH_LIBRARY_URL = "https://ll.thespacedevs.com/2.3.0/launches/upcoming/?limit=5&mode=detailed"
CACHE_FILE = os.path.join(os.path.dirname(__file__), "launch_cache.json")
CACHE_DURATION_SECS = 30 * 60

FALLBACK_LAUNCHES = [
    {
        "id": "fallback-starlink",
        "name": "Falcon 9 | Starlink Mission",
        "net": "2026-06-05T12:00:00+00:00",
        "mission": {"name": "Starlink", "description": "Fallback launch entry used when Launch Library is unavailable.", "orbit": {"name": "Low Earth Orbit", "abbrev": "LEO"}},
        "rocket": {"configuration": {"full_name": "Falcon 9 Block 5"}},
        "pad": {"name": "SLC-40", "latitude": "28.5619", "longitude": "-80.5772", "location": {"name": "Cape Canaveral SFS, FL, USA"}},
        "image": None,
        "status": {"name": "Placeholder"},
    }
]


def _read_cache() -> Dict[str, Any] | None:
    if not os.path.exists(CACHE_FILE):
        return None
    try:
        with open(CACHE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


def _write_cache(payload: Dict[str, Any]) -> None:
    try:
        with open(CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump({"saved_at": time.time(), "payload": payload}, f)
    except Exception:
        pass


def _fetch_launch_library() -> Dict[str, Any]:
    req = urllib.request.Request(
        LAUNCH_LIBRARY_URL,
        headers={"User-Agent": "Collision-Risk-Visualizer/1.0"},
    )
    with urllib.request.urlopen(req, timeout=12) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _trajectory_for_launch(item: Dict[str, Any]) -> List[Dict[str, float]]:
    pad = item.get("pad") or {}
    try:
        lat = float(pad.get("latitude"))
        lon = float(pad.get("longitude"))
    except (TypeError, ValueError):
        lat, lon = 0.0, 0.0

    orbit = ((item.get("mission") or {}).get("orbit") or {}).get("abbrev") or "LEO"
    target_alt = {"LEO": 550, "MEO": 20200, "GTO": 35786, "GEO": 35786, "SSO": 650}.get(orbit.upper(), 550)
    inclination_hint = 28.0 if abs(lat) < 30 else abs(lat)

    return [
        {
            "lat": round(lat + inclination_hint * 0.08 * step, 4),
            "lon": round(((lon + step * 7.0 + 180.0) % 360.0) - 180.0, 4),
            "altitude_km": round(target_alt * (step / 7) ** 1.4, 2),
        }
        for step in range(8)
    ]


def _normalize_launch(item: Dict[str, Any]) -> Dict[str, Any]:
    mission = item.get("mission") or {}
    orbit = mission.get("orbit") or {}
    rocket = (item.get("rocket") or {}).get("configuration") or {}
    pad = item.get("pad") or {}
    net = item.get("net")
    seconds_until = None
    try:
        launch_time = datetime.fromisoformat(net.replace("Z", "+00:00")).astimezone(timezone.utc)
        seconds_until = int((launch_time - datetime.now(timezone.utc)).total_seconds())
    except Exception:
        pass

    return {
        "id": item.get("id"),
        "name": item.get("name"),
        "net": net,
        "seconds_until": seconds_until,
        "status": (item.get("status") or {}).get("name"),
        "mission_name": mission.get("name"),
        "mission_description": mission.get("description"),
        "rocket": rocket.get("full_name") or rocket.get("name"),
        "orbit": orbit.get("abbrev") or orbit.get("name"),
        "pad_name": pad.get("name"),
        "location": (pad.get("location") or {}).get("name"),
        "pad_latitude": pad.get("latitude"),
        "pad_longitude": pad.get("longitude"),
        "image": item.get("image"),
        "trajectory": _trajectory_for_launch(item),
    }


def get_upcoming_launches(limit: int = 5) -> Dict[str, Any]:
    cache = _read_cache()
    if cache and time.time() - cache.get("saved_at", 0) < CACHE_DURATION_SECS:
        raw = cache.get("payload", {})
        source = "cache"
    else:
        try:
            raw = _fetch_launch_library()
            _write_cache(raw)
            source = "launch_library_2"
        except Exception:
            raw = {"results": FALLBACK_LAUNCHES}
            source = "fallback"

    launches = [_normalize_launch(item) for item in raw.get("results", [])[:limit]]
    return {"launches": launches, "count": len(launches), "source": source}
