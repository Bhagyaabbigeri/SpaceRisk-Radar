import os
import sys
import time
import threading
from datetime import datetime, timezone
from typing import Optional
from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
from flask_socketio import SocketIO
import logging

# Ensure root workspace directory is in the python path to resolve local backend module imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import project modules
from backend.tle_fetcher import get_tles
from backend.orbit_calculator import (
    calculate_orbit_state,
    get_inclination_from_tle,
    get_satellite_metadata,
    get_satellite_country,
)
from backend.risk_engine import find_conjunctions
from backend.ground_station import compute_ground_visibility
from backend.heatmap import compute_orbital_heatmap
from backend.kessler import simulate_kessler_risk
from backend.launches import get_upcoming_launches
from backend.maneuvers import get_maneuver_predictions
from backend.alerts import alert_dispatcher, alert_scheduler
from backend.api_v1 import create_api_v1_blueprint
from backend.cache_layer import cache_layer

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Resolve frontend directory relative to project root
FRONTEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'frontend'))

app = Flask(__name__, static_folder=FRONTEND_DIR, static_url_path='')
# Enable CORS for all routes
CORS(app)
# Socket.IO server for pushing realtime updates to connected clients
socketio = SocketIO(app, cors_allowed_origins='*', async_mode='threading')

# Global variables for TLE storage and thread safety
GLOBAL_TLES = []
TLES_LOCK = threading.Lock()

# New: Optimization Cache for Dashboard performance
GLOBAL_STATE = {
    "objects": [],
    "satellites": [],
    "conjunctions": [],
    "stats": {},
    "timestamp": None
}
GLOBAL_STATE_LOCK = threading.Lock()

# Limit how many TLEs are propagated for realtime visualization and screening
# Increased from 300 to 2000 to allow more objects to be plotted (higher CPU/memory cost)
PROPAGATION_LIMIT = 2000
THRESHOLD_LOCK = threading.Lock()
CONJUNCTION_THRESHOLD_KM = 500.0
LAST_CONJUNCTIONS = []
LAST_CONJUNCTIONS_LOCK = threading.Lock()
LAST_KESSLER = {}
LAST_KESSLER_LOCK = threading.Lock()


def _get_threshold() -> float:
    with THRESHOLD_LOCK:
        return CONJUNCTION_THRESHOLD_KM


def _set_threshold(km: float) -> float:
    global CONJUNCTION_THRESHOLD_KM
    with THRESHOLD_LOCK:
        CONJUNCTION_THRESHOLD_KM = max(10.0, min(5000.0, float(km)))
        return CONJUNCTION_THRESHOLD_KM


def _parse_propagation_time(at_param: Optional[str]) -> datetime:
    if not at_param:
        return datetime.now(timezone.utc)
    try:
        t = datetime.fromisoformat(at_param.replace("Z", "+00:00"))
        if t.tzinfo is None:
            t = t.replace(tzinfo=timezone.utc)
        return t.astimezone(timezone.utc)
    except ValueError:
        return datetime.now(timezone.utc)


def _classify_orbit(alt_km: float) -> str:
    if alt_km < 2000.0:
        return "LEO"
    if alt_km < 35000.0:
        return "MEO"
    if alt_km < 36500.0:
        return "GEO"
    return "HEO"


def _build_object_entry(tle, state, socket_format: bool = False) -> dict:
    alt = state.altitude_km
    meta = get_satellite_metadata(tle.name, tle.line1, tle.line2)
    entry = {
        "name": tle.name,
        "norad_id": meta["norad_id"],
        "object_id": meta["object_id"],
        "launch_date": meta["launch_date"],
        "operator": meta["operator"],
        "decay_date": meta["decay_date"],
        "tle_epoch": meta["tle_epoch"],
        "orbit": _classify_orbit(alt),
        "inclination": get_inclination_from_tle(tle.line2),
        "country": get_satellite_country(tle.name),
        "speed_kms": state.speed_kms,
        "timestamp": state.timestamp,
        "tle_line1": tle.line1,
        "tle_line2": tle.line2,
    }
    if socket_format:
        entry["lat"] = state.latitude
        entry["lon"] = state.longitude
        entry["alt_km"] = state.altitude_km
    else:
        entry["latitude"] = state.latitude
        entry["longitude"] = state.longitude
        entry["altitude_km"] = state.altitude_km
    return entry


def _inject_test_debris(objects: list, satellites: list, socket_format: bool = False) -> None:
    if not objects:
        return
    first = objects[0]
    if socket_format:
        lat, lon, alt = first["lat"], first["lon"], first["alt_km"]
        debris_obj = {
            "name": "TEST_DEBRIS_X",
            "lat": round(lat + 0.8, 6),
            "lon": round(lon + 0.8, 6),
            "alt_km": round(alt + 10.0, 2),
            "speed_kms": round(first.get("speed_kms", 0) - 0.05, 4),
            "orbit": first.get("orbit", "LEO"),
            "inclination": first.get("inclination", 51.6),
            "country": "Debris",
            "norad_id": None,
            "object_id": None,
            "launch_date": "N/A",
            "operator": "Simulated",
            "decay_date": "N/A",
            "tle_epoch": None,
            "timestamp": first.get("timestamp"),
        }
    else:
        lat, lon, alt = first["latitude"], first["longitude"], first["altitude_km"]
        debris_obj = {
            "name": "TEST_DEBRIS_X",
            "latitude": round(lat + 0.8, 6),
            "longitude": round(lon + 0.8, 6),
            "altitude_km": round(alt + 10.0, 2),
            "speed_kms": round(first.get("speed_kms", 0) - 0.05, 4),
            "orbit": first.get("orbit", "LEO"),
            "inclination": first.get("inclination", 51.6),
            "country": "Debris",
            "norad_id": None,
            "object_id": None,
            "launch_date": "N/A",
            "operator": "Simulated",
            "decay_date": "N/A",
            "tle_epoch": None,
            "timestamp": first.get("timestamp"),
        }
    objects.append(debris_obj)
    satellites.append({
        "name": debris_obj["name"],
        "latitude": debris_obj.get("lat") or debris_obj.get("latitude"),
        "longitude": debris_obj.get("lon") or debris_obj.get("longitude"),
        "altitude_km": debris_obj.get("alt_km") or debris_obj.get("altitude_km"),
        "speed_kms": debris_obj.get("speed_kms"),
        "operator": debris_obj.get("operator"),
        "orbit": debris_obj.get("orbit"),
        "inclination": debris_obj.get("inclination"),
        "country": debris_obj.get("country"),
    })


def _propagate_catalog(tles_copy: list, dt: datetime, limit: int = PROPAGATION_LIMIT, socket_format: bool = False):
    objects = []
    satellites = []
    for tle in tles_copy[:limit]:
        try:
            state = calculate_orbit_state(tle.line1, tle.line2, dt)
            obj = _build_object_entry(tle, state, socket_format=socket_format)
            objects.append(obj)
            satellites.append({
                "name": obj["name"],
                "latitude": obj.get("lat") or obj.get("latitude"),
                "longitude": obj.get("lon") or obj.get("longitude"),
                "altitude_km": obj.get("alt_km") or obj.get("altitude_km"),
                "speed_kms": obj.get("speed_kms"),
                "operator": obj.get("operator"),
                "orbit": obj.get("orbit"),
                "inclination": obj.get("inclination"),
                "country": obj.get("country"),
            })
        except Exception as e:
            logger.debug(f"Failed to propagate satellite {tle.name}: {e}")
    _inject_test_debris(objects, satellites, socket_format=socket_format)
    return objects, satellites


def _format_conjunctions(conjs_raw: list) -> list:
    conjs = []
    for c in conjs_raw:
        level = c.get("risk_level", "LOW")
        color = c.get("risk_color", "#00f0ff")
        conjs.append({
            "obj1": c.get("sat1"),
            "obj2": c.get("sat2"),
            "sat1": c.get("sat1"),
            "sat2": c.get("sat2"),
            "distance_km": c.get("distance_km"),
            "probability": c.get("probability", 1e-8),
            "probability_pct": c.get("probability_pct", "0.000001%"),
            "risk_factors": c.get("risk_factors", []),
            "evasion_maneuver": c.get("evasion_maneuver", "N/A"),
            "details": c.get("details"),
            "risk": {"level": level, "color": color},
        })
    return conjs


@socketio.on("set_threshold")
def on_set_threshold(data):
    try:
        km = float((data or {}).get("threshold_km", 500.0))
        applied = _set_threshold(km)
        socketio.emit("threshold_updated", {"threshold_km": applied}, broadcast=True)
    except (TypeError, ValueError):
        logger.warning("Invalid threshold payload from client")


def tle_update_worker():
    """
    Background worker thread function that runs indefinitely,
    refreshing the global TLE data from Celestrak every 10 minutes.
    """
    global GLOBAL_TLES
    logger.info("Starting background TLE refresh loop...")
    while True:
        try:
            logger.info("Background thread checking for TLE updates...")
            # get_tles respects the local 2-hour file cache to prevent Celestrak 403 bans
            tles = get_tles()
            if tles:
                with TLES_LOCK:
                    GLOBAL_TLES = tles
                logger.info(f"Background thread updated global state. {len(tles)} active TLEs in memory.")
            else:
                logger.warning("Background thread fetched empty TLE list; keeping existing TLEs in memory.")
        except Exception as e:
            logger.error(f"Error in background TLE updater: {e}")
        
        # Sleep for 10 minutes (600 seconds)
        time.sleep(600)


def emit_objects_worker():
    """
    Background worker that propagates a slice of the TLE catalog and
    emits the live object list to connected Socket.IO clients every few seconds.
    """
    global GLOBAL_TLES
    logger.info("Starting Socket.IO objects emitter thread...")
    while True:
        with TLES_LOCK:
            tles_copy = list(GLOBAL_TLES)

        if tles_copy:
            dt = datetime.now(timezone.utc)
            objects, satellites = _propagate_catalog(
                tles_copy, dt, limit=PROPAGATION_LIMIT, socket_format=True
            )
            threshold = _get_threshold()

            # 1) Emit propagated objects to clients
            try:
                socketio.emit('objects', objects, broadcast=True)
            except Exception as e:
                logger.debug(f"Socket emit (objects) error: {e}")

            # 2) Screen conjunctions and emit
            try:
                conjs_raw = find_conjunctions(satellites, threshold_km=threshold)
                conjs = _format_conjunctions(conjs_raw)
                with LAST_CONJUNCTIONS_LOCK:
                    LAST_CONJUNCTIONS[:] = conjs
                conjs_payload = {
                    'conjunctions': conjs,
                    'count': len(conjs),
                    'threshold_km': threshold,
                    'timestamp': dt.isoformat()
                }
                socketio.emit('conjunctions', conjs_payload, broadcast=True)
            except Exception as e:
                logger.debug(f"Socket emit (conjunctions) error: {e}")

            # 3) Compute lightweight stats and emit
            try:
                alts = [s['altitude_km'] for s in satellites if s.get('altitude_km') is not None]
                avg_alt = (sum(alts) / len(alts)) if alts else 0.0
                min_alt = min(alts) if alts else 0.0
                speeds = [o.get('speed_kms') for o in objects if o.get('speed_kms') is not None]
                max_speed = max(speeds) if speeds else 0.0

                leo_count = sum(1 for a in alts if a < 2000.0)
                meo_count = sum(1 for a in alts if 2000.0 <= a < 35000.0)
                geo_count = sum(1 for a in alts if 35000.0 <= a < 36500.0)
                heo_count = len(alts) - leo_count - meo_count - geo_count

                stats_payload = {
                    'total_satellites': len(satellites),
                    'active_conjunctions': len(conjs) if 'conjs' in locals() else 0,
                    'conjunction_threshold_km': threshold,
                    'avg_altitude_km': round(avg_alt, 2),
                    'min_altitude_km': round(min_alt, 2),
                    'max_speed_kms': round(max_speed, 4),
                    'orbit_distribution': {
                        'Low Earth Orbit (LEO)': leo_count,
                        'Medium Earth Orbit (MEO)': meo_count,
                        'Geostationary Orbit (GEO)': geo_count,
                        'High Earth / Elliptical Orbit (HEO)': heo_count
                    },
                    'timestamp': dt.isoformat()
                }

                socketio.emit('stats', stats_payload, broadcast=True)
            except Exception as e:
                logger.debug(f"Socket emit (stats) error: {e}")

            # 4) Update Global State Cache (New Optimization)
            with GLOBAL_STATE_LOCK:
                GLOBAL_STATE["objects"] = objects
                GLOBAL_STATE["satellites"] = satellites
                GLOBAL_STATE["conjunctions"] = conjs
                GLOBAL_STATE["stats"] = stats_payload
                GLOBAL_STATE["timestamp"] = dt.isoformat()

            # 4b) Emit additive advanced-analysis overlays.
            # capped or binned so the live loop remains bounded.
            try:
                visibility_payload = compute_ground_visibility(objects)
                socketio.emit('ground_visibility', visibility_payload, broadcast=True)
            except Exception as e:
                logger.debug(f"Socket emit (ground_visibility) error: {e}")

            try:
                heatmap_payload = compute_orbital_heatmap(objects)
                socketio.emit('heatmap', heatmap_payload, broadcast=True)
            except Exception as e:
                logger.debug(f"Socket emit (heatmap) error: {e}")

            try:
                debris_payload = simulate_kessler_risk(satellites, conjs if 'conjs' in locals() else [])
                with LAST_KESSLER_LOCK:
                    LAST_KESSLER.update(debris_payload)
                socketio.emit('debris_risk', debris_payload, broadcast=True)
            except Exception as e:
                logger.debug(f"Socket emit (debris_risk) error: {e}")

            try:
                maneuver_payload = get_maneuver_predictions(objects, now=dt)
                socketio.emit('maneuvers', maneuver_payload, broadcast=True)
            except Exception as e:
                logger.debug(f"Socket emit (maneuvers) error: {e}")

        # Push frequency: 3 seconds for responsive UI
        time.sleep(3)

@app.route('/', methods=['GET'])
def root():
    """Serve the frontend index.html for the full-stack single-service deployment."""
    return send_from_directory(FRONTEND_DIR, 'index.html')


@app.route('/<path:path>', methods=['GET'])
def serve_static(path):
    """Serve frontend static assets (JS, CSS, images, etc.).
    Falls back to index.html for unknown paths so the SPA works correctly."""
    import os as _os
    target = _os.path.join(FRONTEND_DIR, path)
    if _os.path.isfile(target):
        return send_from_directory(FRONTEND_DIR, path)
    # Fallback: serve index.html for any unrecognised path
    return send_from_directory(FRONTEND_DIR, 'index.html')

@app.route('/health', methods=['GET'])
def health_check():
    """Lightweight health check for Orbital Command integration."""
    with TLES_LOCK:
        count = len(GLOBAL_TLES)
    return jsonify({
        "status": "ok",
        "tracked_objects": count,
        "timestamp": datetime.now(timezone.utc).isoformat()
    })

@app.route('/api/objects', methods=['GET'])
def get_objects():
    """
    Propagated satellite list. Query param `at` (ISO-8601 UTC) for historical replay.
    """
    at_param = request.args.get('at')

    # Optimization: If no time specified, return the latest background calculation
    if not at_param:
        with GLOBAL_STATE_LOCK:
            if GLOBAL_STATE["objects"]:
                return jsonify(GLOBAL_STATE["objects"])

    with TLES_LOCK:
        tles_copy = list(GLOBAL_TLES)

    if not tles_copy:
        return jsonify([])

    dt = _parse_propagation_time(request.args.get('at'))
    cache_key = f"objects:{dt.isoformat()}:{PROPAGATION_LIMIT}:rest"
    cached = cache_layer.get_json(cache_key)
    if cached is not None:
        return jsonify(cached)

    objects, _ = _propagate_catalog(tles_copy, dt, limit=PROPAGATION_LIMIT, socket_format=False)
    cache_layer.set_json(cache_key, objects, ttl_seconds=10)
    return jsonify(objects)


@app.route('/api/satellite', methods=['GET'])
def get_satellite_detail():
    """Detailed catalog + propagated state for one satellite by name."""
    name = (request.args.get('name') or '').strip()
    if not name:
        return jsonify({"error": "name query parameter required"}), 400

    with TLES_LOCK:
        tles_copy = list(GLOBAL_TLES)

    match = None
    name_lower = name.lower()
    for tle in tles_copy:
        if tle.name and tle.name.lower() == name_lower:
            match = tle
            break
    if match is None:
        for tle in tles_copy:
            if tle.name and name_lower in tle.name.lower():
                match = tle
                break

    if match is None:
        return jsonify({"error": "satellite not found", "name": name}), 404

    dt = _parse_propagation_time(request.args.get('at'))
    try:
        state = calculate_orbit_state(match.line1, match.line2, dt)
        detail = _build_object_entry(match, state, socket_format=False)
        return jsonify(detail)
    except Exception as e:
        return jsonify({"error": str(e), "name": match.name}), 500


def _normalize_search_string(s: str) -> str:
    if not s:
        return ""
    # Map look-alike characters to support fonts where O/0, B/8, etc. are easily confused.
    trans = str.maketrans({
        '0': 'o', '8': 'b', '5': 's', '2': 'z', '1': 'i', 'l': 'i',
        'o': 'o', 'b': 'b', 's': 's', 'z': 'z', 'i': 'i'
    })
    return s.lower().translate(trans)


@app.route('/api/search', methods=['GET'])
def api_search():
    """
    Search the full TLE catalog by satellite name (case-insensitive substring).
    Query params: 'q' or 'name'. Returns up to 10 matched propagated states.
    """
    q = request.args.get('q') or request.args.get('name') or ''
    q = q.strip()
    if not q:
        return jsonify({"matches": [], "count": 0, "query": q})

    with TLES_LOCK:
        tles_copy = list(GLOBAL_TLES)

    dt = _parse_propagation_time(request.args.get('at'))
    q_norm = _normalize_search_string(q)
    matches = []

    for tle in tles_copy:
        try:
            if not tle.name:
                continue
            tle_name_norm = _normalize_search_string(tle.name)
            if q_norm in tle_name_norm:
                state = calculate_orbit_state(tle.line1, tle.line2, dt)
                matches.append({
                    "name": tle.name,
                    "latitude": state.latitude,
                    "longitude": state.longitude,
                    "altitude_km": state.altitude_km,
                    "speed_kms": state.speed_kms,
                    "timestamp": state.timestamp
                })
                if len(matches) >= 10:
                    break
        except Exception:
            # If propagation fails for a specific TLE just skip it
            continue

    return jsonify({"matches": matches, "count": len(matches), "query": q})

@app.route('/api/conjunctions', methods=['GET'])
def get_conjunctions():
    """
    Conjunctions under threshold km. Query: threshold, at (ISO-8601 UTC).
    """
    threshold = request.args.get('threshold', default=_get_threshold(), type=float)
    at_param = request.args.get('at')

    # Optimization: return background result if no 'at'
    if not at_param:
        with GLOBAL_STATE_LOCK:
            if GLOBAL_STATE["conjunctions"]:
                return jsonify({
                    "conjunctions": GLOBAL_STATE["conjunctions"],
                    "count": len(GLOBAL_STATE["conjunctions"]),
                    "threshold_km": threshold,
                    "timestamp": GLOBAL_STATE["timestamp"]
                })

    with TLES_LOCK:
        tles_copy = list(GLOBAL_TLES)

    if not tles_copy:
        return jsonify({
            "conjunctions": [],
            "count": 0,
            "threshold_km": threshold,
            "timestamp": datetime.now(timezone.utc).isoformat()
        })

    dt = _parse_propagation_time(request.args.get('at'))
    cache_key = f"conjunctions:{dt.isoformat()}:{threshold}:{PROPAGATION_LIMIT}"
    cached = cache_layer.get_json(cache_key)
    if cached is not None:
        return jsonify(cached)

    _, satellites = _propagate_catalog(tles_copy, dt, limit=PROPAGATION_LIMIT, socket_format=False)
    conjs_raw = find_conjunctions(satellites, threshold_km=threshold)
    conjs = _format_conjunctions(conjs_raw)
    payload = {
        "conjunctions": conjs,
        "count": len(conjs),
        "threshold_km": threshold,
        "timestamp": dt.isoformat()
    }
    cache_layer.set_json(cache_key, payload, ttl_seconds=20)
    return jsonify(payload)

@app.route('/api/stats', methods=['GET'])
def get_stats():
    """
    Calculates and returns orbital stats and distribution details 
    across LEO, MEO, GEO, and HEO space environments.
    """
    threshold = request.args.get('threshold', default=_get_threshold(), type=float)
    at_param = request.args.get('at')

    # Optimization: return background result if no 'at'
    if not at_param:
        with GLOBAL_STATE_LOCK:
            if GLOBAL_STATE["stats"]:
                return jsonify(GLOBAL_STATE["stats"])

    with TLES_LOCK:
        tles_copy = list(GLOBAL_TLES)

    if not tles_copy:
        return jsonify({
            "total_satellites": 0,
            "active_conjunctions": 0,
            "conjunction_threshold_km": threshold,
            "avg_altitude_km": 0.0,
            "min_altitude_km": 0.0,
            "max_speed_kms": 0.0,
            "orbit_distribution": {},
            "timestamp": datetime.now(timezone.utc).isoformat()
        })

    dt = _parse_propagation_time(request.args.get('at'))
    cache_key = f"stats:{dt.isoformat()}:{threshold}:{PROPAGATION_LIMIT}"
    cached = cache_layer.get_json(cache_key)
    if cached is not None:
        return jsonify(cached)

    objects, satellites = _propagate_catalog(
        tles_copy, dt, limit=PROPAGATION_LIMIT, socket_format=False
    )
    altitudes = [o.get("altitude_km") for o in objects if o.get("altitude_km") is not None]
    speeds = [o.get("speed_kms") for o in objects if o.get("speed_kms") is not None]
    leo_count = sum(1 for a in altitudes if a < 2000.0)
    meo_count = sum(1 for a in altitudes if 2000.0 <= a < 35000.0)
    geo_count = sum(1 for a in altitudes if 35000.0 <= a < 36500.0)
    heo_count = len(altitudes) - leo_count - meo_count - geo_count

    conjs_raw = find_conjunctions(satellites, threshold_km=threshold)
    conjs = conjs_raw

    avg_alt = sum(altitudes) / len(altitudes) if altitudes else 0.0
    max_speed = max(speeds) if speeds else 0.0
    min_alt = min(altitudes) if altitudes else 0.0

    payload = {
        "total_satellites": len(satellites),
        "active_conjunctions": len(conjs),
        "conjunction_threshold_km": threshold,
        "avg_altitude_km": round(avg_alt, 2),
        "min_altitude_km": round(min_alt, 2),
        "max_speed_kms": round(max_speed, 4),
        "orbit_distribution": {
            "Low Earth Orbit (LEO)": leo_count,
            "Medium Earth Orbit (MEO)": meo_count,
            "Geostationary Orbit (GEO)": geo_count,
            "High Earth / Elliptical Orbit (HEO)": heo_count
        },
        "timestamp": dt.isoformat()
    }
    cache_layer.set_json(cache_key, payload, ttl_seconds=20)
    return jsonify(payload)


@app.route('/api/ground-visibility', methods=['GET'])
def get_ground_visibility():
    """Ground station line-of-sight visibility for the propagated catalog."""
    with TLES_LOCK:
        tles_copy = list(GLOBAL_TLES)

    if not tles_copy:
        return jsonify({"stations": [], "visible": [], "visible_count": 0})

    dt = _parse_propagation_time(request.args.get('at'))
    cache_key = f"ground_visibility:{dt.isoformat()}:{PROPAGATION_LIMIT}"
    cached = cache_layer.get_json(cache_key)
    if cached is not None:
        return jsonify(cached)

    objects, _ = _propagate_catalog(tles_copy, dt, limit=PROPAGATION_LIMIT, socket_format=False)
    payload = compute_ground_visibility(objects)
    payload["timestamp"] = dt.isoformat()
    cache_layer.set_json(cache_key, payload, ttl_seconds=20)
    return jsonify(payload)


@app.route('/api/maneuvers', methods=['GET'])
def get_maneuvers():
    """ISS/Hubble maneuver prediction inputs and trajectory previews."""
    with TLES_LOCK:
        tles_copy = list(GLOBAL_TLES)

    if not tles_copy:
        return jsonify({"maneuvers": [], "count": 0, "horizon_days": 30})

    dt = _parse_propagation_time(request.args.get('at'))
    cache_key = f"maneuvers:{dt.isoformat()}:{PROPAGATION_LIMIT}"
    cached = cache_layer.get_json(cache_key)
    if cached is not None:
        return jsonify(cached)

    objects, _ = _propagate_catalog(tles_copy, dt, limit=PROPAGATION_LIMIT, socket_format=False)
    payload = get_maneuver_predictions(objects, now=dt)
    payload["timestamp"] = dt.isoformat()
    cache_layer.set_json(cache_key, payload, ttl_seconds=60)
    return jsonify(payload)


@app.route('/api/debris-risk', methods=['GET'])
def get_debris_risk():
    """Cascading debris risk simulation seeded by current conjunctions."""
    threshold = request.args.get('threshold', default=_get_threshold(), type=float)
    at_param = request.args.get('at')

    # Optimization: return background result if no 'at'
    if not at_param:
        with LAST_KESSLER_LOCK:
            if LAST_KESSLER:
                payload = dict(LAST_KESSLER)
                payload["threshold_km"] = threshold
                payload["timestamp"] = datetime.now(timezone.utc).isoformat()
                return jsonify(payload)

    with TLES_LOCK:
        tles_copy = list(GLOBAL_TLES)

    if not tles_copy:
        return jsonify({"clouds": [], "event_count": 0, "chain_probability_sum": 0.0})

    dt = _parse_propagation_time(request.args.get('at'))
    cache_key = f"debris_risk:{dt.isoformat()}:{threshold}:{PROPAGATION_LIMIT}"
    cached = cache_layer.get_json(cache_key)
    if cached is not None:
        return jsonify(cached)

    _, satellites = _propagate_catalog(tles_copy, dt, limit=PROPAGATION_LIMIT, socket_format=False)
    conjs = find_conjunctions(satellites, threshold_km=threshold)
    payload = simulate_kessler_risk(satellites, conjs)
    payload["threshold_km"] = threshold
    payload["timestamp"] = dt.isoformat()
    cache_layer.set_json(cache_key, payload, ttl_seconds=30)
    return jsonify(payload)


@app.route('/api/launches', methods=['GET'])
def get_launches():
    """Upcoming launches from Launch Library 2 with local fallback."""
    limit = request.args.get('limit', default=5, type=int)
    limit = max(1, min(10, limit))
    cache_key = f"launches:{limit}"
    cached = cache_layer.get_json(cache_key)
    if cached is not None:
        return jsonify(cached)
    payload = get_upcoming_launches(limit=limit)
    cache_layer.set_json(cache_key, payload, ttl_seconds=30 * 60)
    return jsonify(payload)


@app.route('/api/heatmap', methods=['GET'])
def get_heatmap():
    """Orbital congestion heatmap binned by location, altitude band, and orbit."""
    with TLES_LOCK:
        tles_copy = list(GLOBAL_TLES)

    if not tles_copy:
        return jsonify({"cells": [], "max_density": 0, "orbit_counts": {}})

    dt = _parse_propagation_time(request.args.get('at'))
    cache_key = f"heatmap:{dt.isoformat()}:{PROPAGATION_LIMIT}"
    cached = cache_layer.get_json(cache_key)
    if cached is not None:
        return jsonify(cached)

    objects, _ = _propagate_catalog(tles_copy, dt, limit=PROPAGATION_LIMIT, socket_format=False)
    payload = compute_orbital_heatmap(objects)
    payload["timestamp"] = dt.isoformat()
    cache_layer.set_json(cache_key, payload, ttl_seconds=30)
    return jsonify(payload)


def _latest_conjunctions_for_alerts() -> list:
    with LAST_CONJUNCTIONS_LOCK:
        return list(LAST_CONJUNCTIONS)


@app.route('/api/v1/ephemeris/<int:norad_id>', methods=['GET'])
def get_ephemeris_v1(norad_id):
    """Retrieve propagated state vectors for a requested time window."""
    start_str = request.args.get('start')
    end_str = request.args.get('end')
    step = request.args.get('step_sec', default=60, type=int)

    with TLES_LOCK:
        from backend.orbit_calculator import parse_norad_id
        match = next((t for t in GLOBAL_TLES if parse_norad_id(t.line1) == norad_id), None)

    if not match:
        return jsonify({"error": "satellite not found"}), 404

    try:
        from datetime import timedelta
        start = _parse_propagation_time(start_str)
        end = _parse_propagation_time(end_str)

        points = []
        curr = start
        while curr <= end:
            state = calculate_orbit_state(match.line1, match.line2, curr)
            points.append(state.to_dict())
            curr += timedelta(seconds=step)
            # Safety break for massive windows
            if len(points) > 1000:
                break

        return jsonify(points)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/v1/collision-risk/<int:norad_id>', methods=['GET'])
def get_collision_risk_v1(norad_id):
    """Retrieve collision risk details for a specific satellite from latest screening."""
    with TLES_LOCK:
        from backend.orbit_calculator import parse_norad_id
        match = next((t for t in GLOBAL_TLES if parse_norad_id(t.line1) == norad_id), None)

    if not match:
        return jsonify({"error": "satellite not found"}), 404

    name = match.name
    with LAST_CONJUNCTIONS_LOCK:
        risk_event = next((c for c in LAST_CONJUNCTIONS if c["sat1"] == name or c["sat2"] == name), None)

    if not risk_event:
        return jsonify({"status": "nominal", "message": "No active conjunctions detected"}), 200

    return jsonify(risk_event)


app.register_blueprint(create_api_v1_blueprint({
    "objects": get_objects,
    "satellite": get_satellite_detail,
    "search": api_search,
    "conjunctions": get_conjunctions,
    "stats": get_stats,
    "ground_visibility": get_ground_visibility,
    "maneuvers": get_maneuvers,
    "debris_risk": get_debris_risk,
    "launches": get_launches,
    "heatmap": get_heatmap,
    "ephemeris": get_ephemeris_v1,
    "collision_risk": get_collision_risk_v1,
}))

if __name__ == '__main__':
    # 1. Load TLEs in a background thread so the server starts immediately
    # and passes the Render/Railway health check without timing out.
    def _startup_tle_load():
        logger.info("Background startup: loading TLE cache...")
        try:
            global GLOBAL_TLES
            with TLES_LOCK:
                GLOBAL_TLES = get_tles()
            logger.info(f"Background startup complete. Loaded {len(GLOBAL_TLES)} satellites.")
        except Exception as se:
            logger.error(f"Background startup TLE load failed: {se}")

    startup_thread = threading.Thread(target=_startup_tle_load, daemon=True)
    startup_thread.start()
    logger.info("TLE background loader spawned.")

    # 2. Spin up the background thread to refresh the catalog every 10 minutes
    update_thread = threading.Thread(target=tle_update_worker, daemon=True)
    update_thread.start()
    logger.info("Background thread spawned.")
    # 2b. Start emitter thread that pushes propagated positions to clients
    emitter_thread = threading.Thread(target=emit_objects_worker, daemon=True)
    emitter_thread.start()
    logger.info("Socket.IO emitter thread spawned.")

    # Start Flask-SocketIO server
    alert_scheduler.start(_latest_conjunctions_for_alerts, interval_seconds=300)
    logger.info("Alert monitoring scheduler spawned.")

    logger.info("Starting Flask application server...")
    try:
        routes = sorted([r.rule for r in app.url_map.iter_rules()])
        logger.info(f"Registered routes: {routes}")
    except Exception:
        logger.debug("Failed to enumerate routes")

    port = int(os.environ.get('PORT', 5000))
    socketio.run(app, host='0.0.0.0', port=port, debug=False, allow_unsafe_werkzeug=True)
