# 🛰️ SpaceRisk Radar — Complete Interview Guide

> Open `http://localhost:5000` while reading this. Point to each section on screen as you explain it. Everything below is in plain, normal English — no jargon.

---

## What Is This Project?

**SpaceRisk Radar** is an orbital collision-risk screening dashboard. It propagates up to 2,000 catalog objects per cycle, screens their current positions for close approaches, and shows the results on an interactive 3D globe. A synthetic test object is also added to exercise the risk display.

**Why does this matter?** Close approaches are worth screening, but a single position snapshot does not predict an impact. This project visualizes conjunction screening and illustrative cascading-risk estimates for awareness and education; it is not an operational collision-avoidance system.

---

## How It Is Built — Two Parts

### 1. The Backend (Server)
**File:** `backend/app.py`

This is a **Python program** that runs silently in the background. It does four things:
- Checks the TLE cache every 10 minutes and attempts a network fetch when a healthy cache is older than 2 hours
- Uses SGP4 to propagate up to 2,000 catalog TLEs to a requested time
- Screens pairwise 3D distances and assigns heuristic risk scores
- Sends all this data to the browser every **3 seconds** automatically

### 2. The Frontend (Browser Dashboard)
**Files:** `frontend/index.html`, `frontend/ui.js`, `frontend/globe.js`

This is everything you see in the browser. It:
- Draws the interactive 3D globe
- Shows all the data panels (left, right, bottom, top)
- Refreshes automatically every 3 seconds without you doing anything

---

## 🌍 Feature 1 — The 3D Globe (Centre of Screen)

**Point to:** The spinning Earth with coloured dots moving across it.

Each dot represents a propagated catalog object, with a synthetic test object added when a catalog object propagates successfully. Positions are estimates from TLE data and SGP4, not live measurements.

**You can interact with it:**
- **Click + drag** → rotate the globe
- **Scroll wheel** → zoom in or out
- **+ / − buttons** on screen → zoom in or out
- **Circular arrow button** → resets the camera back to the default view
- **Click any dot** → selects that satellite and shows its full details in the left panel

The live view can show up to 2,000 catalog objects per cycle. The frontend creates individual Three.js mesh objects for satellites; the project does not guarantee a particular frame rate.

### 🎨 Visual Guide: What Do The Dots, Lines & Shapes Mean?

| Element | Visual | What It Represents |
|---|---|---|
| **Cyan Dots** | `Cyan (#00f0ff)` | **Low Earth Orbit (LEO)** satellites (< 2,000 km altitude, e.g., ISS, Starlink). |
| **Green Dots** | `Green (#00ff88)` | Objects in the app's HEO altitude category. |
| **Purple Dots** | `Purple (#8855ff)` | Objects in the app's MEO altitude category. |
| **Orange Dots** | `Orange (#ffaa00)` | **Geostationary Orbit (GEO)** satellites (~35,786 km altitude). |
| **Bright Lime Dots** | `Neon Green (#10ff9c)` | Satellites currently **visible to a ground station** by the app's line-of-sight calculation. |
| **Gold Glowing Dots** | `Gold (#ffd700)` | Satellites added to your **Favorites / Watchlist**. |
| **Red Pulsing Dots** | `Red (#ff3b30)` | Satellites involved in a **CRITICAL or HIGH** risk classification. |
| **Red Straight Lines** | `Red Line` | **Conjunction Line** — connects a pair flagged by current 3D separation below the screening threshold. |
| **Red Wireframe Spheres** | `Red Mesh Sphere` | **Kessler Estimate** — illustrative 250 km-radius region around a hypothetical collision point. |
| **Yellow Curved Arcs** | `Yellow Path (#ffcc00)` | **Launch Preview** — an illustrative path generated from launch-pad coordinates and a target-orbit estimate. |
| **Purple Curved Arcs** | `Purple Path (#a855f7)` | **Maneuver Preview** — an 8-point illustrative trajectory for configured ISS/Hubble scenarios. |
| **White Cones on Earth** | `White Cone` | **Ground Station Locations** used for visibility analysis: White Sands, Goldstone DSN, Madrid DSN, Canberra DSN, and Sriharikota. |
| **Cyan Grid & Atmosphere** | `Cyan Net Lines` | **Atmospheric Wireframe Grid** — latitude/longitude reference net around Earth. |

---

## 📡 Feature 2 — Live Satellite Data (TLE Feed)

**What feeds the dots on the globe?**

The backend fetches orbital element data from **CelesTrak**. The data format is called **TLE (Two-Line Element)** — a standardised format describing an object's orbit at a specific epoch. Not every object in the catalog is necessarily propagated in a given cycle.

**Example TLE (what raw data looks like):**
```
ISS (ZARYA)
1 25544U 98067A   24001.50000000  .00000000  00000-0  00000-0 0    01
2 25544  51.6400 000.0000 0001000   0.0000 000.0000 15.50000000000003
```

To estimate a position, the backend runs a TLE through **SGP4**. Given a TLE and a timestamp, the model returns an estimated state that the app converts to latitude, longitude, and altitude.

**What if the internet goes down?**
- All downloaded TLE data is saved locally to `backend/tle_cache.txt`
- If CelesTrak is unreachable, the system uses any available saved TLE file
- The app can continue propagating from an available saved TLE file; the dashboard does not display a guaranteed cache-status flag
- **Cache rule:** it replaces the TLE cache only if the new download has *more* TLE objects than the existing cache

---

## 📊 Feature 3 — Header Stats Bar (Top of Screen)

**Point to:** The row of numbers across the very top.

| Number shown | What it means |
|---|---|
| **Total Objects** | How many propagated catalog objects and the synthetic test object are currently rendered on the globe |
| **Active Threats** | How many object pairs are currently within the screening threshold |
| **Max Speed** | The fastest orbital speed among the currently propagated objects, in km/s |
| **Orbit LEO** | Count of objects in Low Earth Orbit — below ~2,000 km altitude |
| **Orbit GEO** | Count of objects in Geostationary Orbit — at ~36,000 km altitude |

These numbers update automatically every 3 seconds.

---

## 📋 Feature 4 — Ground Visibility Panel (Left Panel, Upper Section)

**Point to:** The "GROUND VISIBILITY" section in the left panel.

**What it shows:** Which propagated satellites are above a ground station's minimum elevation mask in the current snapshot.

**The concept — elevation masking:**
A ground station is counted as having visibility when a satellite is above its 10° minimum elevation mask.

The system calculates this geometry for propagated objects against the five ground stations each update cycle.

**Ground stations monitored:**
| Station | Location |
|---|---|
| White Sands | New Mexico, USA |
| Goldstone DSN | California, USA |
| Madrid DSN | Spain |
| Canberra DSN | Australia |
| Sriharikota | India |

Each entry in the list shows: satellite name, which station can see it, the elevation angle in degrees, and how long the contact window lasts in minutes.

---

## 🚀 Feature 5 — Launch Watch (Left Panel, Lower Section)

**Point to:** The "LAUNCH WATCH" section showing upcoming rocket launches.

**What it does:** Shows up to five upcoming launch entries with a countdown when the launch time is available.

**Where the data comes from:** The **Launch Library 2 API**, which the app queries for launch schedule data.

It shows: rocket name, mission name, launch pad location, target orbit, and seconds until launch. Successful API responses are cached for 30 minutes; a static fallback entry is used if fetching fails.

---

## 🛰️ Feature 6 — Satellite Telemetry Detail (Left Panel — after clicking a satellite)

**Point to:** Click any dot on the globe, then point to the detail panel that appears.

When you click a satellite, the left panel switches from the overview to a full data readout for that specific object. It shows:

**Identity section:**
- Name, classification (payload / rocket body / debris), country or agency that owns it

**Catalog Specifications:**
- **NORAD ID** — a unique number assigned to every tracked object in space by the US Space Command
- **International Designator** — a second ID showing launch year + sequence number

**Orbital Mechanics:**
- Current altitude in km, latitude, longitude
- Orbital inclination — the angle of the orbit relative to Earth's equator

**Velocity Diagnostics:**
- Current orbital speed in km/s

**Conjunction Threat (if applicable):**
- If this satellite is in a close-approach situation, this section shows the other object's name, the distance between them in km, and the heuristic probability score

**Advanced Risk Layers:**
- Debris cloud count near this satellite's region
- Chain-reaction probability score
- Heatmap density at this orbital altitude

---

## ⚠️ Feature 7 — Conjunction Warning Stream (Bottom Panel — scroll down)

**Point to:** The horizontal row of red-bordered cards at the bottom of the page.

**What is a conjunction?**
A conjunction is when two space objects are closer than the screening threshold in the current propagated snapshot. The default threshold is **500 km**.

**What each card tells you:**
- **Risk level badge** — CRITICAL / HIGH / MEDIUM / LOW (red = critical, orange = high, yellow = medium, cyan = low)
- **Object names** — which two objects are involved, e.g. `ONEWEB-0033 ↔ METOP-C`
- **Miss distance** — exactly how far apart they currently are in km
- **Probability badge** — the calculated collision probability as a percentage

**How is the probability calculated?**
The heuristic starts from distance, then adjusts for:
- The pair's average orbital speed
- Whether either object's name, operator, or country value contains "debris"
- Whether both inclinations fall in the model's 70°–110° range
- Orbit type (LEO or GEO)

**The Conjunction Threshold slider:**
In the left **CONTROL FILTERS** panel, the **Conjunction Threshold** slider ranges from 10 km to 2,000 km. The backend accepts and clamps values from 10 km to 5,000 km. The conjunction stream title updates to show the applied threshold.

**Clicking a card:**
Clicking any conjunction card instantly selects that satellite pair on the globe, highlights the approach line between them, and fills the telemetry panel with that satellite's full risk details.

---

## 🔥 Feature 8 — Kessler Syndrome Simulator

**Point to:** The "Debris Clouds" and "Chain Probability" fields in the telemetry panel.

**What is Kessler Syndrome?**
If two objects collide in orbit, the impact creates hundreds of new debris fragments. Those fragments fly outward and can hit other satellites, creating even more debris — a runaway chain reaction that could make that entire orbital band permanently dangerous or unusable. This is Kessler Syndrome.

**What the simulator does:**
It takes up to five conjunction pairs with the smallest current separations and estimates what a hypothetical collision could look like.

For each pair it estimates:
- **Debris count** — a deterministic value calculated from miss distance, not a physical fragmentation model
- **Cloud radius** — a 250 km sphere around the midpoint of the two positions
- **Affected satellites** — other propagated objects within that radius and their illustrative distance-based chain scores
- **Chain probability sum** — the sum of the included affected-object chain scores

The results feed the numbers you see in the telemetry panel:
- **Debris Clouds:** how many hypothetical conjunction events were estimated
- **Chain Probability:** the sum of illustrative chain scores
- **Heatmap Peak:** maximum orbital density in the affected zone

---

## 🕐 Feature 9 — Orbit Timeline 24H Replay (Bottom Panel)

**Point to:** The control bar with LIVE, 15M, play, pause buttons.

This lets you replay estimated satellite positions over the past 24 hours.

| Control | What it does |
|---|---|
| **LIVE** | Returns to real-time mode — satellites at their actual current positions right now |
| **⏪ 15M** | Moves the simulation clock back by 15 minutes |
| **▶ Play** | Starts playing back from the rewound point at the selected speed |
| **⏸ Pause** | Freezes replay at the current simulated moment |
| **Speed selector** | 60× / 300× / 900× / 3600× — how fast to play. At 300×, one real second = 5 minutes of orbital time |
| **Slider** | Drag to any specific moment in the last 24 hours |

**How does this work?**
The timeline slider covers the previous 24 hours. The API's `at` parameter can request propagation at other parseable times; results remain estimates based on the available TLE.

---

## 🔴 Feature 10 — Real-Time Updates (WebSocket Connection)

**In plain terms:** The dashboard does not refresh the page. The browser connects to the Python backend using Socket.IO, and the backend pushes updates every 3 seconds while the client is connected.

**Technology used:** Socket.IO, which can use a persistent WebSocket connection when supported.

The backend pushes seven recurring data event types:
- `objects` → updated satellite positions for the globe
- `conjunctions` → updated close-approach warning cards
- `stats` → updated numbers for the header bar
- `ground_visibility` → ground-station visibility results
- `heatmap` → orbital-density grid
- `debris_risk` → illustrative Kessler estimates
- `maneuvers` → configured maneuver previews

**Why is this better than regular HTTP requests?**

The server pushes updates every 3 seconds to connected clients using Socket.IO, rather than requiring the browser to poll for each update.

With a persistent Socket.IO connection, the server can push updates without requiring the browser to request each update.

---

## 🗄️ Caching Summary

The app uses local caches for TLE data and launch responses. TLE refresh checks run every 10 minutes, and a fetch is normally attempted when the TLE cache is older than 2 hours; launch API responses are cached for 30 minutes. An available TLE file and the launch fallback are used in their respective failure cases.

| Data | Cache file | How long cached |
|---|---|---|
| Satellite TLE orbital data | `backend/tle_cache.txt` | Checked every 10 minutes; network fetch normally after 2 hours |
| Upcoming rocket launches | `backend/launch_cache.json` | 30 minutes |

---

## 🛠️ Full Tech Stack

| Part | Technology | Why |
|---|---|---|
| Backend language | **Python 3** | Readable, great scientific libraries |
| Web framework | **Flask** | Lightweight HTTP server |
| Real-time push | **Flask-SocketIO** | Socket.IO updates to connected browsers |
| Orbital propagation | **SGP4 algorithm** | Estimates positions from TLE data |
| Satellite data | **CelesTrak** | Public TLE catalog source |
| Launch data | **Launch Library 2 API** | Real global launch schedule database |
| 3D rendering | **Three.js (WebGL)** | GPU-accelerated 3D in the browser |
| Frontend | **Vanilla JavaScript + CSS** | No framework dependency, fast load |
| Database | **SQLite** | User accounts, watchlists, preferences |

---

## 💬 Interview Q&A — Quick Answers

---

**Q: Why WebSockets instead of normal HTTP API calls?**

Socket.IO lets the server push its 3-second updates to connected clients, rather than requiring a separate browser poll for each update.

---

**Q: How do you show 2,000+ satellites without the browser freezing?**

The live view can propagate up to 2,000 catalog objects per cycle. The current globe creates individual Three.js meshes, so rendering speed depends on the device and is not specified as a fixed frame rate.

---

**Q: How does the collision probability get calculated?**

The conjunction engine first calculates 3D separation using a Haversine surface distance combined with the altitude difference. The heuristic probability score then uses that distance, the average orbital speed, orbit type, debris-name/operator/country matches, and whether both inclinations are between 70° and 110°. It does not use covariance or an operational collision-probability model.

---

**Q: What if CelesTrak goes offline?**

The TLE fetcher can use a saved local TLE file when a network fetch is unavailable. Which objects can be propagated still depends on the available catalog data.

---

**Q: What is SGP4?**

SGP4 stands for Simplified General Perturbations model 4. It propagates a TLE to an estimated position at a requested time. SpaceRisk Radar uses the `python-sgp4` library and converts the propagated state to latitude, longitude, altitude, and speed.

---

**Q: What is a TLE?**

Two-Line Element set. A standardized three-line text format consisting of a name line and two data lines. It encodes orbital elements for a specific epoch; SGP4 uses those elements to estimate a position at a requested time.

---

## ▶️ How to Run the Project

```bash
# From the project root — start the app, which also serves the frontend
python backend/app.py

# Open in browser
http://localhost:5000
```

Flask serves both the API and static frontend from **port 5000**; no second frontend server is required.
