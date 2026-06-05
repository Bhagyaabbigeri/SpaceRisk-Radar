from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Iterable, List


SCHEDULED_MANEUVERS = [
    {
        "satellite": "ISS",
        "display_name": "ISS Reboost Planning Window",
        "source": "local prediction input",
        "scheduled_utc": "2026-06-08T03:20:00+00:00",
        "delta_v_mps": 0.55,
        "altitude_delta_km": 1.6,
        "confidence": "planning",
        "notes": "Public ISS reboost schedule data is not exposed as a stable API; replace this provider with NASA OEM/operator data when available.",
    },
    {
        "satellite": "HST",
        "display_name": "Hubble Drag Compensation Scenario",
        "source": "local prediction input",
        "scheduled_utc": "2026-06-18T14:00:00+00:00",
        "delta_v_mps": 0.18,
        "altitude_delta_km": 0.5,
        "confidence": "scenario",
        "notes": "Hubble routine maneuver details are not published through a general public schedule API.",
    },
]


def _parse_time(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc)


def _matches_satellite(name: str, token: str) -> bool:
    name_upper = (name or "").upper()
    token_upper = token.upper()
    if token_upper == "ISS":
        return "ISS" in name_upper or "ZARYA" in name_upper
    if token_upper == "HST":
        return "HST" in name_upper or "HUBBLE" in name_upper
    return token_upper in name_upper


def get_maneuver_predictions(
    objects: Iterable[Dict[str, Any]],
    now: datetime | None = None,
    horizon_days: int = 30,
) -> Dict[str, Any]:
    now = (now or datetime.now(timezone.utc)).astimezone(timezone.utc)
    horizon = now + timedelta(days=horizon_days)
    objects_list = list(objects)
    predictions = []

    for maneuver in SCHEDULED_MANEUVERS:
        scheduled = _parse_time(maneuver["scheduled_utc"])
        if scheduled < now - timedelta(days=1) or scheduled > horizon:
            continue

        match = next(
            (obj for obj in objects_list if _matches_satellite(obj.get("name", ""), maneuver["satellite"])),
            None,
        )
        if not match:
            continue

        alt = match.get("altitude_km", match.get("alt_km", 0.0)) or 0.0
        lat = match.get("latitude", match.get("lat", 0.0)) or 0.0
        lon = match.get("longitude", match.get("lon", 0.0)) or 0.0
        delta_alt = maneuver["altitude_delta_km"]

        # Lightweight trajectory preview for the frontend animation layer.
        preview = []
        for step in range(8):
            fraction = step / 7
            preview.append({
                "lat": round(float(lat), 4),
                "lon": round(((float(lon) + 360.0 * fraction + 180.0) % 360.0) - 180.0, 4),
                "altitude_km": round(float(alt) + delta_alt * fraction, 2),
                "phase": round(fraction, 3),
            })

        predictions.append({
            **maneuver,
            "scheduled_utc": scheduled.isoformat(),
            "seconds_until": int((scheduled - now).total_seconds()),
            "current_altitude_km": round(float(alt), 2),
            "predicted_altitude_km": round(float(alt) + delta_alt, 2),
            "trajectory_preview": preview,
        })

    return {"maneuvers": predictions, "count": len(predictions), "horizon_days": horizon_days}
