# 🛰️ SpaceRisk Radar — Complete Project Architecture & Technical Guide

---

## 📑 Table of Contents
1. [Step 1: How to Run the Project](#step-1-how-to-run-the-project)
2. [Step 2: Project Structure](#step-2-project-structure)
3. [Step 3: Frontend Architecture](#step-3-frontend-architecture)
4. [Step 4: Backend Architecture & Request Lifecycle](#step-4-backend-architecture--request-lifecycle)
5. [Step 5: Core APIs Specification](#step-5-core-apis-specification)
6. [Step 6: Frontend → Backend End-to-End Communication Flows](#step-6-frontend--backend-end-to-end-communication-flows)
7. [Step 7: External APIs & Data Sources](#step-7-external-apis--data-sources)
8. [Step 8: Database Architecture](#step-8-database-architecture)
9. [Step 9: Real-World Testing & Debugging Case Study](#step-9-real-world-testing--debugging-case-study)

---

## Step 1: How to Run the Project

### 1.1 Environment Setup (Run once from workspace root `d:\SpaceRisk-Rader`)
```powershell
# Create Python virtual environment
python -m venv .venv

# Activate virtual environment (Windows)
.venv\Scripts\activate

# Install required dependencies
pip install -r requirements.txt
```

### 1.2 Terminal 1 — Backend Server
```powershell
cd d:\SpaceRisk-Rader
.venv\Scripts\activate
python backend/app.py
```
* **Host**: `http://localhost:5000`
* Starts Flask REST API, Flask-SocketIO WebSocket server, and background worker threads (TLE catalog refresh & live telemetry emission).

### 1.3 Terminal 2 — Frontend Server
```powershell
cd d:\SpaceRisk-Rader\frontend
python -m http.server 8000
```
* **Host**: `http://localhost:8000`
* Serves the static HTML/CSS/JS frontend dashboard.

### 1.4 Database / Services
* **Database**: SQLite 3 is embedded — no separate database server or Docker service needs to be started. The database file (`backend/app_data.db`) is initialized automatically on first run.

---

## Step 2: Project Structure

```
SpaceRisk-Radar/
├── frontend/                               # Client-side presentation layer
│   ├── index.html                          # Main entry HTML file & HUD layout
│   ├── ui.js                               # UI state, event handling, API/Socket communication
│   ├── globe.js                            # Three.js 3D Earth & orbit rendering engine
│   ├── earth_cyber_texture.png             # Cyberpunk Earth procedural texture map
│   ├── screenshot.png                      # Application visual showcase
│   └── vendor/                             # Offline fallback libraries
│       ├── socket.io.min.js                # Socket.IO client library
│       ├── socket.io.local.js              # Socket.IO local fallback connector
│       └── ionicons.local.js               # Ionicons offline script fallback
│
├── backend/                                # Server-side API & computation engine
│   ├── app.py                              # Main backend entry, Flask app, Socket.IO & core routes
│   ├── api_v1.py                           # Versioned Blueprint routes (Auth, preferences, OpenAPI docs)
│   ├── orbit_calculator.py                 # SGP4/SDP4 satellite orbit propagation physics
│   ├── risk_engine.py                      # Conjunction proximity screening & collision probability
│   ├── tle_fetcher.py                      # CelesTrak TLE catalog ingestion & local caching
│   ├── ground_station.py                   # Ground station line-of-sight visibility calculator
│   ├── heatmap.py                          # Orbital spatial density binning
│   ├── kessler.py                          # Monte Carlo Kessler syndrome debris cascade model
│   ├── launches.py                         # Launch Library 2 ingestion & trajectory modeling
│   ├── maneuvers.py                        # B-star orbital decay & station-keeping predictions
│   ├── alerts.py                           # Automated threshold breach detection & webhook dispatcher
│   ├── auth_service.py                     # SQLite database manager, password hashing, JWT auth
│   ├── cache_layer.py                      # In-memory TTL caching with Redis optional backend
│   ├── openapi_spec.py                     # OpenAPI 3.0 specification definition
│   ├── app_data.db                         # SQLite database file
│   └── tle_cache.txt                       # Local cache for CelesTrak TLEs
│
├── tools/                                  # Testing, diagnostic & inspection scripts
│   ├── check_frontend.py                   # Frontend server validator
│   ├── check_objects.py                    # Orbit propagation validator
│   ├── inspect_app.py                      # Route & configuration inspection
│   └── search_nisar.py                     # Search query verification utility
│
├── requirements.txt                        # Python dependencies
└── README.md                               # Project documentation
```

---

## Step 3: Frontend Architecture

### 3.1 Framework & Core Technologies
* **Framework**: **Vanilla JavaScript (ES6+), HTML5, and Vanilla CSS3** (no heavy framework like React, Vue, Angular, or Next.js).
* **3D Graphics Engine**: **Three.js (r128)** for WebGL hardware-accelerated globe and orbit rendering.
* **Real-time Protocol**: **Socket.IO Client** for bidirectional WebSocket events.
* **Icons & Fonts**: **Ionicons** + Google Fonts (**Orbitron** and **Rajdhani**).

### 3.2 Main Entry File
* **HTML Entry**: `frontend/index.html`
* **Script Entries**: `frontend/ui.js` (UI logic & networking) and `frontend/globe.js` (3D scene orchestration).

### 3.3 Main Components / Panels
The interface is a single-page Cyberpunk HUD Dashboard structured into distinct functional modules:
1. **3D Interactive Globe (`#globe-container`)**: Procedural Earth sphere with atmosphere shader, starfields, satellite coordinate meshes, ground station cones, and conjunction threat lines.
2. **Telemetry & Live Metric Cards**: Top summary HUD (`#stat-sats`, `#stat-threats`, `#stat-avg-alt`, `#stat-max-speed`, orbit distribution bars).
3. **Fuzzy Search & Autocomplete (`#search-name`, `#search-results`)**: Debounced real-time catalog search.
4. **Orbital Filter Controls**: LEO, MEO, GEO, ALL filter buttons, Altitude range slider, Inclination slider, Country/Agency selector.
5. **Detailed Satellite Telemetry Panel (`#telemetry-panel`)**: NORAD ID, operator, launch date, TLE epoch, exact geodetic coordinates, speed, and closest approach parameters.
6. **Conjunction Warning Stream (`#conjunctions-list`)**: Live cards displaying object pairs, miss distance, risk level, and collision probability.
7. **Advanced SSA Layer Panels**:
   * Ground Station Visibility passes (`#ground-visibility-list`)
   * Orbital Congestion Heatmap (`#heatmap-max-density`)
   * Kessler Debris Cloud cascade analysis (`#debris-cloud-count`)
   * Upcoming Rocket Launches countdown (`#launch-list`)
   * Orbital Maneuver predictions (`#maneuver-list`)
8. **Historical Timeline & Replay Bar (`#playback-panel`)**: 24-hour time scrubber for historical and future orbital propagation.
9. **User Auth & Watchlist Modal (`#auth-panel`)**: JWT login/signup with custom threshold configuration.

### 3.4 API Communication Method
* **Native browser `fetch()` API** with `async`/`await` for all REST request-response cycles.
* **Socket.IO `io(API_BASE)`** for real-time WebSocket event streams.
* **No `axios` or external HTTP wrapper** is used.

> ### 🎙️ Interview Summary Pitch:
> *"The frontend is built using **Vanilla JavaScript, HTML5, and CSS with Three.js for 3D WebGL rendering**. The application starts from **`frontend/index.html`** which bootstraps **`ui.js`** and **`globe.js`**. The main UI is organized into **glassmorphic HUD panels including a 3D Earth canvas, live telemetry cards, conjunction warning stream, advanced mission layers, and a historical playback timeline**. API communication happens through **native browser `fetch()` for REST endpoints and Socket.IO for real-time WebSocket data streaming**."*

---

## Step 4: Backend Architecture & Request Lifecycle

### 4.1 Framework & Entry File
* **Framework**: **Flask 2.2+ (Python)** paired with **Flask-SocketIO / Eventlet** for asynchronous WebSocket handling.
* **Backend Entry File**: `backend/app.py`

### 4.2 Where Routes are Defined
* **Core REST & WebSocket Routes**: In `backend/app.py` (e.g. `/api/objects`, `/api/conjunctions`, `/api/search`, `/api/stats`).
* **Versioned User, Auth & OpenAPI Blueprint**: In `backend/api_v1.py` registered under prefix `/api/v1/*`.

### 4.3 Where Actual Processing Happens
* Orbital mechanics calculations are executed in `backend/orbit_calculator.py` using the **SGP4/SDP4 algorithm**.
* Conjunction screening and collision probability ($P_c$) are calculated in `backend/risk_engine.py`.
* CelesTrak TLE fetching and caching are processed in `backend/tle_fetcher.py`.
* Database transactions and JWT authentication are processed in `backend/auth_service.py`.

### 4.4 End-to-End Request Lifecycle Trace

```
1. HTTP / WebSocket Request (from Browser)
   │
   ▼
2. Flask Router (@app.route in backend/app.py or @bp.route in backend/api_v1.py)
   │
   ▼
3. Input Parsing & Validation (Query params `q`, `at`, `threshold`, or JSON body)
   │
   ▼
4. Cache Verification (Check `cache_layer.py` or precomputed `GLOBAL_STATE`)
   ├── [Cache HIT] ──► Return cached JSON immediately (< 2ms)
   └── [Cache MISS] ──► Proceed to Processing Engine
         │
         ▼
5. Computation / Domain Engine:
   ├── SGP4 Propagation (`orbit_calculator.py`)
   ├── 3D Distance & Probability Screening (`risk_engine.py`)
   ├── External Data Fetch / Mirror Fallback (`tle_fetcher.py` / `launches.py`)
   └── SQLite Database Query / Mutation (`auth_service.py`)
         │
         ▼
6. Response Serialization (`jsonify(payload)` / `emit(event, data)`)
   │
   ▼
7. Client-side Handler (`ui.js` / Three.js canvas update)
```

---

## Step 5: Core APIs Specification

### 5.1 API Summary Table

| Method | Endpoint | Frontend Caller | Backend Handler | What it returns |
| :--- | :--- | :--- | :--- | :--- |
| **`GET`** | **`/api/objects`** | `loadSatellites()` in `ui.js` | `get_objects()` in `app.py` | Array of objects containing real-time geodetic coordinates (`lat`, `lon`, `alt_km`, `speed_kms`, `orbit`, `country`, `norad_id`). |
| **`GET`** | **`/api/conjunctions`** | `loadConjunctions()` in `ui.js` | `get_conjunctions()` in `app.py` | List of orbital pairs with close approaches under threshold, miss distance, risk level, collision probability ($P_c$), and evasion maneuver suggestions. |
| **`GET`** | **`/api/search`** | `setupSearch()` in `ui.js` | `api_search()` in `app.py` | Top 10 matching satellites matching query string with instant propagated coordinates. |
| **`GET`** | **`/api/stats`** | `loadStats()` in `ui.js` | `get_stats()` in `app.py` | System-wide orbital statistics: active satellites count, threat count, average altitude, max speed, and LEO/GEO distribution. |
| **`POST`** | **`/api/v1/auth/login`** | `submitAuth('login')` in `ui.js` | `login()` in `api_v1.py` | JWT authentication token and user profile object. |

---

### 5.2 Deep-Dive API: `GET /api/conjunctions` (Orbital Collision Risk Screening)

#### Why this is the core API:
It performs pairwise spatial proximity screening across active space objects and applies statistical collision probability modeling ($P_c$).

#### Request Structure:
* **Method**: `GET`
* **URL**: `http://localhost:5000/api/conjunctions`
* **Query Parameters**:
  * `threshold` *(optional float)*: Maximum miss distance in kilometers to flag as a threat (Default: `500.0`).
  * `at` *(optional ISO-8601 string)*: Target timestamp for historical replay or future prediction (e.g. `2026-08-19T12:00:00Z`).

#### Processing Algorithm:
1. **Time Resolution**: Parses `at` query parameter into a UTC `datetime` object.
2. **State Propagation**: Propagates satellite TLEs to epoch $t$ using the `SGP4` propagator in `backend/orbit_calculator.py`.
3. **3D Spatial Distance Calculation (`haversine_3d`)**:
   $$d_{3D} = \sqrt{d_{\text{haversine}}^2 + (\Delta \text{altitude})^2}$$
4. **Collision Probability ($P_c$) & Risk Weighting (`calculate_collision_probability`)**:
   * Base score: $\log_{10}(P_c) = -2.0 - 0.08 \times d_{\text{3D}}$
   * Congestion factor: $+0.3$ multiplier for Low Earth Orbit (LEO).
   * Velocity factor: Scales based on closing speed.
   * Controllability penalty: $+0.6$ penalty if one or both objects are uncontrolled space debris.
5. **Risk Classification**:
   * 🔴 **CRITICAL**: Distance $< 25\text{ km}$ or $P_c \ge 0.001$
   * 🟠 **HIGH**: Distance $< 75\text{ km}$
   * 🟡 **MEDIUM**: Distance $< 200\text{ km}$
   * 🟢 **LOW**: Distance $\ge 200\text{ km}$
6. **Evasion Maneuver Computation**: Suggests recommended delta-v ($\Delta V$) thrust direction and burn magnitude.

#### Response Example:
```json
{
  "conjunctions": [
    {
      "obj1": "STARLINK-1007",
      "obj2": "COSMOS 2251 DEBRIS",
      "distance_km": 14.82,
      "probability": 0.00342,
      "probability_pct": "0.342%",
      "risk": {
        "level": "CRITICAL",
        "color": "#ff3b30",
        "factors": [
          "Ultra-close proximity encounter (<15km)",
          "LEO orbital density multiplier",
          "Uncontrolled space debris element"
        ]
      },
      "evasion_maneuver": "+15.2 m/s radial burn 45m prior to TCA"
    }
  ],
  "count": 1,
  "threshold_km": 500.0,
  "timestamp": "2026-08-19T10:54:02.123456+00:00"
}
```

---

## Step 6: Frontend → Backend End-to-End Communication Flows

### Feature 1: Real-Time Satellite Telemetry & Conjunction Warning Stream

```
[1. User Action]
Browser loads or WebSocket reconnects
      ↓
[2. Frontend Function]
`initSocketOnce()` runs in `frontend/ui.js`
      ↓
[3. Protocol / Event]
Socket.IO connects to `http://127.0.0.1:5000` and registers listener `socket.on('objects', ...)`
      ↓
[4. Backend Worker]
`emit_objects_worker()` in `backend/app.py` runs on a 3-second background thread loop
      ↓
[5. Backend Processing]
Calls `calculate_orbit_state()` via SGP4 in `orbit_calculator.py` and `find_conjunctions()` in `risk_engine.py`
      ↓
[6. Data Push]
Backend emits WebSocket event: `socketio.emit('objects', sat_list)` and `socketio.emit('conjunctions', conj_list)`
      ↓
[7. Frontend State Update]
`plotSatellites(objects)` runs in `ui.js` → updates `allSatData` array
      ↓
[8. Visual Output]
`globe.createSatelliteMesh()` updates Three.js 3D sphere meshes; `renderConjunctions()` renders warning cards in the HUD stream.
```

---

### Feature 2: Satellite Search & Autocomplete Telemetry Inspection

```
[1. User Action]
User types "STARLINK" into the search bar (`#search-name`)
      ↓
[2. Frontend Function]
`setupSearch()` triggers a debounced input listener (160ms) in `frontend/ui.js`
      ↓
[3. HTTP Request]
`fetch('http://127.0.0.1:5000/api/search?q=STARLINK')`
      ↓
[4. Backend Route]
Route `@app.route('/api/search')` dispatches to `api_search()` in `backend/app.py`
      ↓
[5. Backend Processing]
Normalizes search string; searches `GLOBAL_TLES` catalog; propagates matched satellites via SGP4 in `orbit_calculator.py`
      ↓
[6. Response]
Backend returns JSON: `{ matches: [...], count: 10, query: "STARLINK" }`
      ↓
[7. Frontend UI Update]
Renders dropdown list under the search input (`#search-results`)
      ↓
[8. User Click & Focus]
User clicks a match → `showTelemetry(sat)` highlights the satellite in gold on the 3D globe, scales the mesh, and populates the Telemetry HUD panel.
```

---

## Step 7: External APIs & Data Sources

### 1. CelesTrak (Two-Line Element Satellite Catalog)
* **API / URL**: `https://celestrak.org/pub/TLE/catalog.txt`
* **Why needed**: Provides authoritative orbital element sets for all active satellites, debris, and orbital objects.
* **Calling File**: `backend/tle_fetcher.py`
* **Data Returned**: Raw multiline text containing 3-line TLE records (satellite name, line 1, line 2).
* **How Used**: Parsed into `TLE` data structures and passed into SGP4 to compute exact geodetic positions.
* **Failure Handling**:
  * 1st Fallback: Reads from local disk cache `backend/tle_cache.txt`.
  * 2nd Fallback: Queries secondary URL `https://celestrak.org/NORAD/elements/gp.php?GROUP=active&FORMAT=tle`.
  * 3rd Fallback: Queries tertiary AMSAT mirror `https://www.amsat.org/amsat/ftp/keps/current/nasabare.txt`.

### 2. Launch Library 2 (The Space Devs API)
* **API / URL**: `https://ll.thespacedevs.com/2.3.0/launches/upcoming/?limit=5&mode=detailed`
* **Why needed**: Provides upcoming space rocket launch schedules, launch pads, rocket configurations, and target orbits.
* **Calling File**: `backend/launches.py`
* **Data Returned**: Structured JSON with launch mission details, countdown seconds (`net`), and pad coordinates.
* **How Used**: Renders upcoming launch countdowns in the HUD and draws projected ascent trajectory vectors on the 3D globe.
* **Failure Handling**:
  * Reads from local disk cache `backend/launch_cache.json` (30-minute TTL).
  * If API fails and cache is empty, uses hardcoded fallback launch models (`FALLBACK_LAUNCHES`).

---

## Step 8: Database Architecture

### 8.1 Database Type & File
* **Database Engine**: **SQLite 3** (`sqlite3`)
* **Storage Location**: `backend/app_data.db` (configurable via `CRV_AUTH_DB` environment variable)
* **Connection Manager**: `AuthService` class in `backend/auth_service.py`

### 8.2 Database Tables & Schema

```sql
-- 1. User accounts and roles
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    display_name TEXT,
    role TEXT NOT NULL DEFAULT 'user',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

-- 2. User alert thresholds, webhook integrations, and HUD settings
CREATE TABLE IF NOT EXISTS preferences (
    user_id INTEGER PRIMARY KEY,
    preferences_json TEXT NOT NULL,
    alert_threshold_km REAL NOT NULL DEFAULT 50.0,
    email_alerts_enabled INTEGER NOT NULL DEFAULT 0,
    webhook_url TEXT,
    FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- 3. Favorited and monitored satellites per user
CREATE TABLE IF NOT EXISTS watched_satellites (
    user_id INTEGER NOT NULL,
    satellite_name TEXT NOT NULL,
    created_at TEXT NOT NULL,
    PRIMARY KEY(user_id, satellite_name),
    FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
);
```

---

## Step 9: Real-World Testing & Debugging Case Study

### 🔍 Real Issue: CelesTrak Rate Limiting & Malformed TLE Parsing Causing Propagation Crashes

#### 1. Issue Identified:
When CelesTrak rate-limited requests or returned transient 503 errors during network hiccups, the orbital propagator received empty/corrupted data. This caused the SGP4 engine to throw mathematical domain errors (`sgp4.api.SGP4Error`), crashing the background position emitter thread and freezing the 3D frontend globe.

#### 2. Investigation:
* Analyzed `backend/backend.log` and `backend/tle_fetcher.py`.
* Discovered that:
  1. `urllib.request` threw `HTTPError: 429 Too Many Requests` or `URLError: [Errno 11001] getaddrinfo failed`.
  2. The parser had no minimum threshold check for valid 3-line TLE blocks.
  3. A failed fetch overwrote the local cache with empty content.

#### 3. Fix & Verification:
* **Multi-Tier Fallback Strategy**:
  1. Added a **3-tier mirror fallback** in `backend/tle_fetcher.py`: CelesTrak Main $\rightarrow$ CelesTrak GP Active $\rightarrow$ AMSAT Mirror.
  2. Added **health validation**: `MIN_HEALTHY_OBJECTS = 100`. If new data has fewer than 100 valid TLE sets, the system rejects the payload and preserves the existing healthy cache.
  3. Added **thread-safe caching & lock management** (`TLES_LOCK`) in `backend/app.py` so background updates never block incoming REST or WebSocket requests.
* **Testing**:
  * Simulated network disconnection by pointing to an invalid dummy URL; verified that the backend seamlessly fell back to `tle_cache.txt` without dropping WebSocket emissions.
  * Ran `python tools/check_objects.py` to verify continuous mathematical propagation of 2000+ objects without runtime errors.
