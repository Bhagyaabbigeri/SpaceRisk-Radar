# API Reference

All REST endpoints are served by the Flask backend at the same origin as the frontend. WebSocket events use Socket.IO.

!!! note
    Routes prefixed `/api/v1/` include versioned aliases and v1-only endpoints such as authentication and ephemeris. Routes prefixed `/api/` are public endpoints.

---

## REST endpoints

### `GET /health`

Lightweight health check endpoint. Returns a 200 OK response when the server is running.

**Request**

```
GET /health
```

**Response**

```json
{
  "status": "ok",
  "tracked_objects": 16128,
  "timestamp": "2026-10-15T12:59:59.101754+00:00"
}
```

Trimmed. Values change every cycle. `tracked_objects` is the loaded catalog count; `/api/stats` reports the propagated batch.

---

### `GET /api/objects`

Propagates up to 2,000 catalog TLEs to the requested time. If `at` is omitted, the target time is the current UTC time.

**Query parameters**

| Parameter | Type | Default | Description |
|---|---|---|---|
| `at` | ISO-8601 string | now | Propagate the selected catalog objects to this UTC time |

**Request**

```
GET /api/objects
```

**Response** — array of objects

```json
[
  {
    "name": "CALSPHERE 1",
    "norad_id": 900,
    "object_id": "063C",
    "launch_date": "~2006 (catalog seq. 3C)",
    "operator": "Other",
    "decay_date": "Active (in catalog)",
    "tle_epoch": "2026-07-22T03:14:37.766112+00:00",
    "orbit": "LEO",
    "inclination": 90.2206,
    "country": "Other",
    "speed_kms": 7.347751678000258,
    "timestamp": "2026-10-15T13:01:09.789525+00:00",
    "lat": 53.306763086485745,
    "lon": -129.20530745169907,
    "alt_km": 1001.0675259375739
  }
]
```

Trimmed. Values change every cycle.

---

### `GET /api/satellite`

Returns propagated state and catalog metadata for a single satellite by name.

**Query parameters**

| Parameter | Type | Required | Description |
|---|---|---|---|
| `name` | string | yes | Satellite name (case-insensitive substring match) |
| `at` | ISO-8601 string | no | Propagate to this time |

**Request**

```
GET /api/satellite?name=ISS
```

**Response** — a satellite object with propagated state and catalog metadata

Trimmed. Values change every cycle. Example `GET /api/satellite?name=ISS` response:

```json
{
  "name": "ISS (ZARYA)",
  "norad_id": 25544,
  "object_id": "067A",
  "orbit": "LEO",
  "inclination": 51.6313,
  "country": "USA/Russia",
  "speed_kms": 7.660677048916251,
  "timestamp": "2026-10-15T13:01:20.296060+00:00",
  "latitude": 44.30840495694562,
  "longitude": 169.53497061154042,
  "altitude_km": 423.1961233613629
}
```

**Error responses**

- `400` — `name` parameter missing
- `404` — no matching satellite found

---

### `GET /api/search`

Searches the full TLE catalog by name. Returns up to 10 matches with propagated positions.

**Query parameters**

| Parameter | Type | Description |
|---|---|---|
| `q` or `name` | string | Search query (case-insensitive substring) |
| `at` | ISO-8601 string | Optional propagation time |

**Request**

```
GET /api/search?q=ISS
```

**Response**

```json
{
  "matches": [
    {
      "name": "ISS (ZARYA)",
      "latitude": 44.304843678145076,
      "longitude": 169.54351932101656,
      "altitude_km": 423.1951414324485,
      "speed_kms": 7.660677339814689,
      "timestamp": "2026-10-15T13:01:20.405838+00:00"
    },
    {
      "name": "ISS (UNITY)",
      "latitude": 44.304843678145076,
      "longitude": 169.54351932101656,
      "altitude_km": 423.1951414324485,
      "speed_kms": 7.660677339814689,
      "timestamp": "2026-10-15T13:01:20.405838+00:00"
    }
  ],
  "count": 10,
  "query": "ISS"
}
```

Trimmed. Values change every cycle.

---

### `GET /api/conjunctions`

Returns pairs of objects within the screening threshold, with risk scores.

**Query parameters**

| Parameter | Type | Default | Description |
|---|---|---|---|
| `threshold` | float (km) | 500.0 | Screening distance. Server clamps to 10–5000 km |
| `at` | ISO-8601 string | now | Propagate to this time |

**Request**

```
GET /api/conjunctions?threshold=200
```

**Response**

```json
{
  "conjunctions": [
    {
      "sat1": "CALSPHERE 1",
      "sat2": "TEST_DEBRIS_X",
      "distance_km": 104.08,
      "probability": 0.00000001,
      "probability_pct": "0.000001%",
      "risk_factors": [
        "LEO orbital density multiplier",
        "Uncontrolled space debris element",
        "Polar orbital intersection node"
      ],
      "risk": {"level": "LOW", "color": "#00f0ff"}
    }
  ],
  "count": 2985,
  "threshold_km": 200.0,
  "timestamp": "2026-10-15T13:01:16.158050+00:00"
}
```

Trimmed. Values change every cycle.

---

### `GET /api/stats`

Returns orbital environment statistics.

**Request**

```
GET /api/stats
```

**Response**

```json
{
  "total_satellites": 1959,
  "active_conjunctions": 2985,
  "conjunction_threshold_km": 500.0,
  "avg_altitude_km": 10417.15,
  "min_altitude_km": 15.02,
  "max_speed_kms": 8.1083,
  "orbit_distribution": {
    "Low Earth Orbit (LEO)": 1352,
    "Medium Earth Orbit (MEO)": 150,
    "Geostationary Orbit (GEO)": 441,
    "High Earth / Elliptical Orbit (HEO)": 16
  },
  "timestamp": "2026-10-15T13:01:16.158050+00:00"
}
```

Trimmed. Values change every cycle.

---

### `GET /api/ground-visibility`

Returns satellites currently visible from each ground station.

**Request**

```
GET /api/ground-visibility
```

**Response**

```json
{
  "stations": [
    {
      "id": "white_sands",
      "name": "White Sands",
      "latitude": 32.5007,
      "longitude": -106.6086,
      "altitude_km": 1.2,
      "min_elevation_deg": 10.0
    },
    {
      "id": "goldstone",
      "name": "Goldstone DSN",
      "latitude": 35.4267,
      "longitude": -116.89,
      "altitude_km": 1.0,
      "min_elevation_deg": 10.0
    }
  ],
  "visible": [
    {
      "satellite": "CALSPHERE 1",
      "station_id": "goldstone",
      "station_name": "Goldstone DSN",
      "elevation_deg": 13.47,
      "duration_seconds": 104
    },
    {
      "satellite": "LCS 1",
      "station_id": "white_sands",
      "station_name": "White Sands",
      "elevation_deg": 28.0,
      "duration_seconds": 889
    }
  ],
  "visible_count": 698,
  "timestamp": "2026-10-15T13:01:21.088162+00:00"
}
```

Trimmed. Values change every cycle.

---

### `GET /api/heatmap`

Returns the orbital congestion density grid.

**Request**

```
GET /api/heatmap
```

**Response**

```json
{
  "cells": [
    {
      "altitude_band_km": [35500, 36000],
      "density": 50,
      "lat": -7.5,
      "lon": -75.0,
      "orbit": "GEO",
      "risk_score": 1.0,
      "satellites": ["TDRS 7", "ASIASTAR", "TDRS 8", "UFO 11 (USA 174)", "SKYNET 5A", "ZHONGXING-9", "SES-7 (PROTOSTAR 2)", "ASIASAT 5"]
    },
    {
      "altitude_band_km": [35500, 36000],
      "density": 49,
      "lat": -7.5,
      "lon": -105.0,
      "orbit": "GEO",
      "risk_score": 0.98,
      "satellites": ["INTELSAT 906 (IS-906)", "THURAYA-2", "ABS-4 (MOBISAT-1)", "SYRACUSE 3A", "METEOSAT-9 (MSG-2)", "THURAYA-3", "TURKSAT 3A", "WGS F2 (USA 204)"]
    }
  ],
  "max_density": 50,
  "orbit_counts": {
    "GEO": 441,
    "HEO": 16,
    "LEO": 1352,
    "MEO": 150
  },
  "timestamp": "2026-10-15T13:01:21.247548+00:00"
}
```

Trimmed. Values change every cycle.

---

### `GET /api/debris-risk`

Returns the Kessler cascade simulation results seeded by the current conjunctions.

**Query parameters**

| Parameter | Type | Default | Description |
|---|---|---|---|
| `threshold` | float (km) | 500.0 | Conjunction threshold used to seed the simulation |

**Request**

```
GET /api/debris-risk
```

**Response**

```json
{
  "clouds": [
    {
      "id": "cloud_1",
      "source": ["ISS (ZARYA)", "ISS (UNITY)"],
      "center": {"lat": 44.4422, "lon": 169.212, "altitude_km": 423.23},
      "radius_km": 250.0,
      "debris_count": 80,
      "primary_probability": 0.0,
      "affected_satellites": []
    }
  ],
  "event_count": 5,
  "chain_probability_sum": 0.0,
  "threshold_km": 500.0,
  "timestamp": "2026-10-15T13:01:21.418719+00:00"
}
```

Trimmed. Values change every cycle.

---

### `GET /api/maneuvers`

Returns configured ISS/Hubble maneuver scenario inputs and lightweight trajectory previews that fall within the 30-day horizon. The response can contain no maneuvers.

**Request**

```
GET /api/maneuvers
```

**Response**

```json
{
  "count": 0,
  "horizon_days": 30,
  "maneuvers": [],
  "timestamp": "2026-10-15T13:01:21.447457+00:00"
}
```

Trimmed. Values change every cycle. This live response contained no in-horizon maneuver scenarios.

---

### `GET /api/launches`

Returns upcoming launches from Launch Library 2. Successful responses are cached locally for 30 minutes; a static fallback entry is used if fetching fails.

**Query parameters**

| Parameter | Type | Default | Description |
|---|---|---|---|
| `limit` | int | 5 | Number of launches to return (clamped to 1–10) |

**Request**

```
GET /api/launches?limit=2
```

**Response**

```json
{
  "count": 2,
  "launches": [
    {
      "name": "Falcon 9 Block 5 | USSF-481",
      "net": "2026-10-15T23:57:05Z",
      "status": "Go for Launch",
      "mission_name": "USSF-481",
      "rocket": "Falcon 9 Block 5",
      "orbit": "PO",
      "location": "Vandenberg SFB, CA, USA"
    },
    {
      "name": "Falcon 9 Block 5 | Bandwagon 5 (Dedicated Mid-Inclination Rideshare)",
      "net": "2026-10-19T10:30:00Z",
      "status": "Go for Launch",
      "mission_name": "Bandwagon 5 (Dedicated Mid-Inclination Rideshare)",
      "rocket": "Falcon 9 Block 5",
      "orbit": "LEO",
      "location": "Cape Canaveral SFS, FL, USA"
    }
  ],
  "source": "launch_library_2"
}
```

Trimmed. Values change every cycle.

---

### `GET /api/v1/ephemeris/<norad_id>`

Returns a time series of propagated state vectors for one satellite.

**Path parameters**

| Parameter | Type | Description |
|---|---|---|
| `norad_id` | integer | NORAD catalog number |

**Query parameters**

| Parameter | Type | Default | Description |
|---|---|---|---|
| `start` | ISO-8601 string | now | Start of the window |
| `end` | ISO-8601 string | now | End of the window |
| `step_sec` | integer | 60 | Step size in seconds. Capped at 1000 points. |

**Request**

```
GET /api/v1/ephemeris/25544?start=2026-10-15T12:00:00Z&end=2026-10-15T12:02:00Z&step_sec=60
```

**Response** — array of state dicts

```json
[
  {
    "latitude": -42.59476030371685,
    "longitude": -93.62014853189316,
    "altitude_km": 425.1200663762356,
    "speed_kms": 7.658116180666227,
    "timestamp": "2026-10-15T12:00:00+00:00"
  },
  {
    "latitude": -44.603505736116546,
    "longitude": -89.05637501571914,
    "altitude_km": 425.76562505831043,
    "speed_kms": 7.657848163228265,
    "timestamp": "2026-10-15T12:01:00+00:00"
  }
]
```

Trimmed. Values change every cycle.

---

### `GET /api/v1/collision-risk/<norad_id>`

Returns the latest conjunction involving a given satellite (from the most recent background screening cycle).

**Response — active conjunction found**

```json
{
  "sat1": "ISS (ZARYA)",
  "sat2": "ISS (UNITY)",
  "obj1": "ISS (ZARYA)",
  "obj2": "ISS (UNITY)",
  "distance_km": 0.0,
  "probability": 0.010790294709353956,
  "probability_pct": "1.079%",
  "risk": {"level": "CRITICAL", "color": "#ff3b30"},
  "risk_factors": [
    "Ultra-close proximity encounter (<10km)",
    "LEO orbital density multiplier",
    "Active coordinated payloads"
  ]
}
```

Trimmed. Values change every cycle.

---

## Authentication endpoints (v1 only)

These endpoints are under `/api/v1/`. Protected routes accept JSON bodies where required. Send the JWT in the header `Authorization: Bearer <token>`. The following responses were captured with a throwaway local test account; JWT values are redacted.

### `POST /api/v1/auth/signup`

```json
{
  "email": "doc-accuracy-2150474f09e94c3487477d43f3cfd0fe@example.invalid",
  "password": "<redacted throwaway password>",
  "display_name": "Docs test"
}
```

Returns `{ "user": {...}, "token": "<jwt>" }` with HTTP 201.

```json
{
  "user": {
    "id": 4,
    "email": "doc-accuracy-2150474f09e94c3487477d43f3cfd0fe@example.invalid",
    "display_name": "Docs test",
    "role": "user",
    "created_at": "2026-10-15T13:04:24.340733+00:00",
    "updated_at": "2026-10-15T13:04:24.340733+00:00"
  },
  "token": "<redacted>"
}
```

---

### `POST /api/v1/auth/login`

```json
{
  "email": "doc-accuracy-2150474f09e94c3487477d43f3cfd0fe@example.invalid",
  "password": "<redacted throwaway password>"
}
```

Returns `{ "user": {...}, "token": "<jwt>", "expires_in": 28800 }`.

```json
{
  "user": {
    "id": 4,
    "email": "doc-accuracy-2150474f09e94c3487477d43f3cfd0fe@example.invalid",
    "display_name": "Docs test",
    "role": "user",
    "created_at": "2026-10-15T13:04:24.340733+00:00",
    "updated_at": "2026-10-15T13:04:24.340733+00:00"
  },
  "token": "<redacted>",
  "expires_in": 28800
}
```

---

### `POST /api/v1/auth/logout`

Requires auth. Returns `{ "ok": true, "message": "discard bearer token client-side" }`. Discard the token client-side.

```json
{"ok": true, "message": "discard bearer token client-side"}
```

---

### `GET /api/v1/auth/me`

Requires auth. Returns `{ "user": {...} }`.

```json
{
  "user": {
    "id": 4,
    "email": "doc-accuracy-2150474f09e94c3487477d43f3cfd0fe@example.invalid",
    "display_name": "Docs test",
    "role": "user",
    "created_at": "2026-10-15T13:04:24.340733+00:00",
    "updated_at": "2026-10-15T13:04:24.340733+00:00"
  }
}
```
---

### `PATCH /api/v1/profile`

Requires auth. Updates display name.

```json
{ "display_name": "Docs Test User" }
```

```json
{
  "user": {
    "id": 4,
    "email": "doc-accuracy-2150474f09e94c3487477d43f3cfd0fe@example.invalid",
    "display_name": "Docs Test User",
    "role": "user",
    "created_at": "2026-10-15T13:04:24.340733+00:00",
    "updated_at": "2026-10-15T13:05:35.052356+00:00"
  }
}
```

---

### `GET /api/v1/preferences`

Requires auth. Returns the user's stored preferences object.

```json
{
  "preferences": {
    "default_orbit_filter": "ALL",
    "show_debris_clouds": true,
    "show_ground_visibility": true,
    "show_heatmap": true,
    "theme": "dark"
  },
  "watched_satellites": [],
  "alert_threshold_km": 50.0,
  "email_alerts_enabled": false,
  "webhook_url": null
}
```
---

### `PUT /api/v1/preferences`

Requires auth. Replaces the preferences object.

```json
{
  "preferences": {
    "default_orbit_filter": "ALL",
    "show_debris_clouds": true,
    "show_ground_visibility": true,
    "show_heatmap": true,
    "theme": "dark"
  },
  "watched_satellites": [],
  "alert_threshold_km": 75.0,
  "email_alerts_enabled": false,
  "webhook_url": null
}
```
---

### `POST /api/v1/watched-satellites`

Requires auth. Adds a satellite to the user's watchlist.

```json
{ "satellite_name": "ISS (ZARYA)" }
```

```json
{
  "preferences": {
    "default_orbit_filter": "ALL",
    "show_debris_clouds": true,
    "show_ground_visibility": true,
    "show_heatmap": true,
    "theme": "dark"
  },
  "watched_satellites": ["ISS (ZARYA)"],
  "alert_threshold_km": 75.0,
  "email_alerts_enabled": false,
  "webhook_url": null
}
```
---

### `DELETE /api/v1/watched-satellites/<name>`

Requires auth. Removes a satellite from the watchlist.

```json
{
  "preferences": {
    "default_orbit_filter": "ALL",
    "show_debris_clouds": true,
    "show_ground_visibility": true,
    "show_heatmap": true,
    "theme": "dark"
  },
  "watched_satellites": [],
  "alert_threshold_km": 75.0,
  "email_alerts_enabled": false,
  "webhook_url": null
}
```
---

## OpenAPI / Swagger UI

The server exposes a machine-readable spec and an interactive UI:

- `GET /api/v1/openapi.json` — OpenAPI 3.0 JSON spec
- `GET /api/v1/docs` — Swagger UI

---

## WebSocket events (Socket.IO)

Connect to the server root with a Socket.IO client. All events below use the default namespace.

### Server → Client

| Event | Emitted every | Payload summary |
|---|---|---|
| `objects` | 3 s | Array of propagated satellite objects |
| `conjunctions` | 3 s | `{ conjunctions, count, threshold_km, timestamp }` |
| `stats` | 3 s | Orbital statistics summary |
| `ground_visibility` | 3 s | `{ stations, visible, visible_count }` |
| `heatmap` | 3 s | Density grid |
| `debris_risk` | 3 s | Kessler cascade result |
| `maneuvers` | 3 s | Maneuver prediction list |
| `threshold_updated` | on change | `{ threshold_km }` — broadcast after a client sends `set_threshold` |

### Client → Server

| Event | Payload | Effect |
|---|---|---|
| `set_threshold` | `{ "threshold_km": 200.0 }` | Updates the server-side conjunction screening distance. Value is clamped to 10–5000 km. Server broadcasts `threshold_updated` to all clients. |
