# API Reference

All REST endpoints are served by the Flask backend at the same origin as the frontend. WebSocket events use Socket.IO.

!!! note
    Routes prefixed `/api/v1/` are versioned aliases or exclusive v1 endpoints (auth, ephemeris, etc.). Routes prefixed `/api/` are the stable public endpoints. The v1 routes mirror the public routes unless noted otherwise.

---

## REST endpoints

### `GET /health`

Lightweight health check. Used by Render to verify the service is alive.

**Request**

```
GET /health
```

**Response**

```json
{
  "status": "ok",
  "tracked_objects": 1842,
  "timestamp": "2024-01-15T12:00:00+00:00"
}
```

---

### `GET /api/objects`

Returns all propagated satellite objects from the most recent background cycle.

**Query parameters**

| Parameter | Type | Default | Description |
|---|---|---|---|
| `at` | ISO-8601 string | now | Propagate all objects to this UTC time instead of the latest background snapshot |

**Request**

```
GET /api/objects
GET /api/objects?at=2024-01-15T12:00:00Z
```

**Response** — array of objects

```json
[
  {
    "name": "ISS (ZARYA)",
    "norad_id": 25544,
    "object_id": "98067A",
    "launch_date": "~1998 (catalog seq. 67)",
    "operator": "USA/Russia",
    "decay_date": "Active (in catalog)",
    "tle_epoch": "2024-01-14T10:22:00+00:00",
    "orbit": "LEO",
    "inclination": 51.64,
    "country": "USA/Russia",
    "speed_kms": 7.66,
    "timestamp": "2024-01-15T12:00:00+00:00",
    "latitude": 42.31,
    "longitude": -87.45,
    "altitude_km": 421.5
  }
]
```

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

**Response** — single object with same fields as `/api/objects`

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
GET /api/search?q=starlink
```

**Response**

```json
{
  "matches": [
    {
      "name": "STARLINK-1234",
      "latitude": 53.2,
      "longitude": 10.4,
      "altitude_km": 550.1,
      "speed_kms": 7.61,
      "timestamp": "2024-01-15T12:00:00+00:00"
    }
  ],
  "count": 10,
  "query": "starlink"
}
```

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
      "sat1": "ISS (ZARYA)",
      "sat2": "TEST_DEBRIS_X",
      "distance_km": 142.3,
      "probability": 0.000214,
      "probability_pct": "0.021400%",
      "risk_level": "HIGH",
      "risk_factors": ["Uncontrolled space debris element", "LEO orbital density multiplier"],
      "evasion_maneuver": "Evasion recommended for ISS (ZARYA): Execute prograde delta-V burn of +0.25 m/s.",
      "details": {
        "sat1_pos": {"lat": 42.31, "lon": -87.45, "alt": 421.5},
        "sat2_pos": {"lat": 43.11, "lon": -86.65, "alt": 431.5}
      },
      "risk": {"level": "HIGH", "color": "#ff7a00"}
    }
  ],
  "count": 1,
  "threshold_km": 200.0,
  "timestamp": "2024-01-15T12:00:00+00:00"
}
```

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
  "total_satellites": 2001,
  "active_conjunctions": 3,
  "conjunction_threshold_km": 500.0,
  "avg_altitude_km": 732.4,
  "min_altitude_km": 184.2,
  "max_speed_kms": 7.92,
  "orbit_distribution": {
    "Low Earth Orbit (LEO)": 1834,
    "Medium Earth Orbit (MEO)": 52,
    "Geostationary Orbit (GEO)": 78,
    "High Earth / Elliptical Orbit (HEO)": 37
  },
  "timestamp": "2024-01-15T12:00:00+00:00"
}
```

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
    }
  ],
  "visible": [
    {
      "satellite": "ISS (ZARYA)",
      "station_id": "white_sands",
      "station_name": "White Sands",
      "elevation_deg": 32.5,
      "duration_seconds": 412
    }
  ],
  "visible_count": 1,
  "timestamp": "2024-01-15T12:00:00+00:00"
}
```

---

### `GET /api/heatmap`

Returns the orbital congestion density grid.

**Request**

```
GET /api/heatmap
```

**Response** — shape of response depends on `heatmap.py` binning logic.

```json
{
  "cells": [...],
  "max_density": 14,
  "orbit_counts": {
    "LEO": 1834,
    "MEO": 52,
    "GEO": 78,
    "HEO": 37
  },
  "timestamp": "2024-01-15T12:00:00+00:00"
}
```

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
      "source": ["ISS (ZARYA)", "TEST_DEBRIS_X"],
      "center": {"lat": 42.71, "lon": -87.05, "altitude_km": 426.5},
      "radius_km": 250.0,
      "debris_count": 223,
      "primary_probability": 0.00531,
      "affected_satellites": [
        {
          "satellite": "SOME-SAT",
          "distance_to_cloud_km": 88.3,
          "chain_probability": 0.00142
        }
      ]
    }
  ],
  "event_count": 1,
  "chain_probability_sum": 0.00142,
  "threshold_km": 500.0,
  "timestamp": "2024-01-15T12:00:00+00:00"
}
```

---

### `GET /api/maneuvers`

Returns maneuver predictions for tracked objects.

**Request**

```
GET /api/maneuvers
```

**Response** — array of maneuver prediction objects (shape defined by `maneuvers.py`).

---

### `GET /api/launches`

Returns upcoming launches from Launch Library 2, with a local fallback cache.

**Query parameters**

| Parameter | Type | Default | Description |
|---|---|---|---|
| `limit` | int | 5 | Number of launches to return (clamped to 1–10) |

**Request**

```
GET /api/launches?limit=3
```

**Response** — array of launch objects (shape defined by `launches.py`).

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
GET /api/v1/ephemeris/25544?start=2024-01-15T12:00:00Z&end=2024-01-15T13:00:00Z&step_sec=60
```

**Response** — array of state dicts

```json
[
  {
    "latitude": 42.31,
    "longitude": -87.45,
    "altitude_km": 421.5,
    "speed_kms": 7.66,
    "timestamp": "2024-01-15T12:00:00+00:00"
  }
]
```

---

### `GET /api/v1/collision-risk/<norad_id>`

Returns the latest conjunction involving a given satellite (from the most recent background screening cycle).

**Response — no active conjunction**

```json
{
  "status": "nominal",
  "message": "No active conjunctions detected"
}
```

**Response — active conjunction found** — same shape as a single conjunction in `/api/conjunctions`.

---

## Authentication endpoints (v1 only)

These endpoints are under `/api/v1/`. They require a JSON body. Protected endpoints require the header `Authorization: Bearer <token>`.

### `POST /api/v1/auth/signup`

```json
{
  "email": "user@example.com",
  "password": "secret",
  "display_name": "Alice"
}
```

Returns `{ "user": {...}, "token": "<jwt>" }` with HTTP 201.

---

### `POST /api/v1/auth/login`

```json
{
  "email": "user@example.com",
  "password": "secret"
}
```

Returns `{ "user": {...}, "token": "<jwt>", "expires_in": 28800 }`.

---

### `POST /api/v1/auth/logout`

Requires auth. Returns `{ "ok": true }`. Discard the token client-side.

---

### `GET /api/v1/auth/me`

Requires auth. Returns `{ "user": {...} }`.

---

### `PATCH /api/v1/profile`

Requires auth. Updates display name.

```json
{ "display_name": "Bob" }
```

---

### `GET /api/v1/preferences`

Requires auth. Returns the user's stored preferences object.

---

### `PUT /api/v1/preferences`

Requires auth. Replaces the preferences object.

---

### `POST /api/v1/watched-satellites`

Requires auth. Adds a satellite to the user's watchlist.

```json
{ "satellite_name": "ISS (ZARYA)" }
```

---

### `DELETE /api/v1/watched-satellites/<name>`

Requires auth. Removes a satellite from the watchlist.

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
