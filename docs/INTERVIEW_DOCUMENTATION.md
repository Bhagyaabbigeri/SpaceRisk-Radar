# 🛰️ SpaceRisk Radar — Complete Interview Guide

> Open `http://localhost:8000` while reading this. Point to each section on screen as you explain it. Everything below is in plain, normal English — no jargon.

---

## What Is This Project?

**SpaceRisk Radar** is a real-time space collision monitoring dashboard. It watches thousands of real satellites and debris objects flying around Earth, detects when two of them are getting dangerously close, and shows everything live on an interactive 3D globe inside your browser.

**Why does this matter?** Right now there are over **10,000 active satellites** and **36,000+ debris fragments** orbiting Earth at around 28,000 km/h. If two objects hit each other, they create thousands of new debris pieces. Those pieces can hit other satellites, creating even more debris — a chain reaction called **Kessler Syndrome** that could make entire orbits unusable for decades. This tool helps predict and visualize those risks before they happen.

---

## How It Is Built — Two Parts

### 1. The Backend (Server)
**File:** `backend/app.py`

This is a **Python program** that runs silently in the background. It does four things:
- Downloads real satellite tracking data from the internet every 2 hours
- Uses orbital physics math to calculate exactly where every satellite is *right now*
- Checks if any two satellites are dangerously close to each other
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

Every single dot on the globe is a **real satellite or debris object** that is currently in orbit. They move in real time based on actual physics calculations.

**You can interact with it:**
- **Click + drag** → rotate the globe
- **Scroll wheel** → zoom in or out
- **+ / − buttons** on screen → zoom in or out
- **Circular arrow button** → resets the camera back to the default view
- **Click any dot** → selects that satellite and shows its full details in the left panel

**How does it show 2,000+ objects smoothly?**
It uses a JavaScript library called **Three.js** which talks directly to the computer's GPU (graphics card). Instead of drawing 2,000 individual objects one by one, it batches all satellite dots into **a single GPU instruction** — so the graphics card renders all of them in one pass. This is why it runs at 60 frames per second without lag.

### 🎨 Visual Guide: What Do The Dots, Lines & Shapes Mean?

| Element | Visual | What It Represents |
|---|---|---|
| **Cyan Dots** | `Cyan (#00f0ff)` | **Low Earth Orbit (LEO)** satellites (< 2,000 km altitude, e.g., ISS, Starlink). |
| **Green Dots** | `Green (#00ff88)` | **Medium / High Earth Orbit (MEO/HEO)** satellites or general debris objects. |
| **Orange Dots** | `Orange (#ffaa00)` | **Geostationary Orbit (GEO)** satellites (~35,786 km altitude). |
| **Bright Lime Dots** | `Neon Green (#10ff9c)` | Satellites currently **visible to a ground station** (line-of-sight active link). |
| **Gold Glowing Dots** | `Gold (#ffd700)` | Satellites added to your **Favorites / Watchlist**. |
| **Red Pulsing Dots** | `Red (#ff3b30)` | Satellites involved in a **CRITICAL or HIGH collision threat**. |
| **Red Straight Lines** | `Red Line` | **Conjunction Threat Line** — connects two satellites passing dangerously close to each other (< threshold km). |
| **Red Wireframe Spheres** | `Red Mesh Sphere` | **Kessler Debris Cloud** — 250 km danger zone showing simulated fragment scatter from a collision. |
| **Yellow Curved Arcs** | `Yellow Path (#ffcc00)` | **Launch Trajectory** — expected orbital path of an upcoming rocket launch. |
| **Purple Curved Arcs** | `Purple Path (#a855f7)` | **Maneuver Path** — predicted trajectory of a satellite performing an orbital maneuver or decay. |
| **White Cones on Earth** | `White Cone` | **Ground Stations** (e.g. Sriharikota, Cape Canaveral, Canberra) tracking satellites. |
| **Cyan Grid & Atmosphere** | `Cyan Net Lines` | **Atmospheric Wireframe Grid** — latitude/longitude reference net around Earth. |

---

## 📡 Feature 2 — Live Satellite Data (TLE Feed)

**What feeds the dots on the globe?**

The backend downloads data from **CelesTrak**, which is NORAD's public satellite tracking database. The data format is called **TLE (Two-Line Element)** — it's a standardised two-line text format that describes a satellite's orbit at a specific point in time. Every tracked object in space has one.

**Example TLE (what raw data looks like):**
```
ISS (ZARYA)
1 25544U 98067A   24001.50000000  .00000000  00000-0  00000-0 0    01
2 25544  51.6400 000.0000 0001000   0.0000 000.0000 15.50000000000003
```

To turn those numbers into a real position, the backend runs them through a physics algorithm called **SGP4** — the same formula used by NORAD and aerospace agencies worldwide. Given a TLE and a timestamp, SGP4 outputs the satellite's current latitude, longitude, and altitude.

**What if the internet goes down?**
- All downloaded TLE data is saved locally to `backend/tle_cache.txt`
- If CelesTrak is unreachable, the system automatically uses the saved file
- The dashboard keeps running fully — it just shows a flag that data is from cache
- **Smart rule:** it only replaces the cache if the new download has *more* satellites than what's already saved, so a bad partial download never degrades coverage

---

## 📊 Feature 3 — Header Stats Bar (Top of Screen)

**Point to:** The row of numbers across the very top.

| Number shown | What it means |
|---|---|
| **Total Objects** | How many satellites/debris are currently rendered on the globe |
| **Active Threats** | How many pairs of objects are dangerously close right now (within your warning threshold) |
| **Max Speed** | The fastest orbital speed recorded among all tracked objects, in km/s |
| **Orbit LEO** | Count of objects in Low Earth Orbit — below ~2,000 km altitude |
| **Orbit GEO** | Count of objects in Geostationary Orbit — at ~36,000 km altitude |

These numbers update automatically every 3 seconds.

---

## 📋 Feature 4 — Ground Visibility Panel (Left Panel, Upper Section)

**Point to:** The "GROUND VISIBILITY" section in the left panel.

**What it shows:** Which satellites are currently in a position where a ground station on Earth could contact them.

**The concept — elevation masking:**
A ground station can only talk to a satellite by radio if the satellite is *above the horizon* from the station's perspective. The minimum angle above the horizon is called the **elevation angle**. If a satellite is below 10 degrees elevation, it's too low — the signal gets blocked by the curvature of the Earth and the atmosphere.

The system calculates this geometry for every satellite against every ground station, every update cycle.

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

**What it does:** Shows the next 5 real upcoming rocket launches worldwide with a live countdown timer.

**Where the data comes from:** The **Launch Library 2 API** — a free, public database maintained by The Space Devs that aggregates global launch schedules from all agencies (SpaceX, ISRO, ESA, etc.).

It shows: rocket name, mission name, launch pad location, target orbit, and seconds until launch. Data is cached locally for 30 minutes so the dashboard doesn't continuously hit the external API.

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
- If this satellite is in a close-approach situation, this section shows the other object's name, the distance between them in km, and the AI-calculated collision probability

**Advanced Risk Layers:**
- Debris cloud count near this satellite's region
- Chain-reaction probability score
- Heatmap density at this orbital altitude

---

## ⚠️ Feature 7 — Conjunction Warning Stream (Bottom Panel — scroll down)

**Point to:** The horizontal row of red-bordered cards at the bottom of the page.

**What is a conjunction?**
A conjunction is when two space objects pass dangerously close to each other. The default warning distance is **500 km**. Any two objects that come within 500 km of each other appear as a warning card here.

**What each card tells you:**
- **Risk level badge** — LOW / MEDIUM / HIGH (colour coded: cyan = low, orange = medium, red = high)
- **Object names** — which two objects are involved, e.g. `ONEWEB-0033 ↔ METOP-C`
- **Miss distance** — exactly how far apart they currently are in km
- **Probability badge** — the calculated collision probability as a percentage

**How is the probability calculated?**
The closer two objects are, the higher the base score. That score is then adjusted by:
- How fast they are moving relative to each other
- Whether the objects are active and controllable, or dead uncontrolled debris
- The angle at which their orbits cross (head-on crossings are riskier)
- How crowded the orbital region is (busier zones = higher base risk)

**The threshold slider:**
On the right panel there is a slider to adjust the warning distance. Move it lower to show only the most urgent threats. Move it higher to see more warnings. The conjunction stream title updates live to show the current threshold.

**Clicking a card:**
Clicking any conjunction card instantly selects that satellite pair on the globe, highlights the approach line between them, and fills the telemetry panel with that satellite's full risk details.

---

## 🔥 Feature 8 — Kessler Syndrome Simulator

**Point to:** The "Debris Clouds" and "Chain Probability" fields in the telemetry panel.

**What is Kessler Syndrome?**
If two objects collide in orbit, the impact creates hundreds of new debris fragments. Those fragments fly outward and can hit other satellites, creating even more debris — a runaway chain reaction that could make that entire orbital band permanently dangerous or unusable. This is Kessler Syndrome.

**What the simulator does:**
It takes the top 5 most dangerous conjunction pairs (the ones with the smallest miss distances) and asks: *what if those two objects actually collided?*

For each pair it calculates:
- **Debris count** — how many fragments the collision would generate (based on miss distance; closer = more energetic impact = more debris)
- **Cloud radius** — a 250 km sphere around the collision point where fragments would scatter
- **Affected satellites** — which other satellites are within that danger zone and what their secondary collision probability is
- **Chain probability sum** — the total probability of secondary collisions cascading further

The results feed the numbers you see in the telemetry panel:
- **Debris Clouds:** how many simulated collision events were modelled
- **Chain Probability:** the overall cascading risk score
- **Heatmap Peak:** maximum orbital density in the affected zone

---

## 🕐 Feature 9 — Orbit Timeline 24H Replay (Bottom Panel)

**Point to:** The control bar with LIVE, 15M, play, pause buttons.

This lets you go back in time and watch where all the satellites *were* in the past 24 hours.

| Control | What it does |
|---|---|
| **LIVE** | Returns to real-time mode — satellites at their actual current positions right now |
| **⏪ 15M** | Moves the simulation clock back by 15 minutes |
| **▶ Play** | Starts playing back from the rewound point at the selected speed |
| **⏸ Pause** | Freezes replay at the current simulated moment |
| **Speed selector** | 60× / 300× / 900× / 3600× — how fast to play. At 300×, one real second = 5 minutes of orbital time |
| **Slider** | Drag to any specific moment in the last 24 hours |

**How does this work?**
The SGP4 orbital physics algorithm does not just calculate where a satellite is *right now*. It can calculate where any satellite was at *any point in time* — past or future — as long as you have its TLE. Replay mode simply tells SGP4 to use a different timestamp instead of the current time.

---

## 🔴 Feature 10 — Real-Time Updates (WebSocket Connection)

**In plain terms:** The dashboard does not refresh the page and does not keep sending "any updates?" requests to the server. Instead, the Python backend and the browser hold a **single permanent open connection** between them, and the backend pushes fresh data down that connection every 3 seconds automatically.

**Technology used:** Socket.IO — a WebSocket library.

The backend pushes three types of data events:
- `objects` → updated satellite positions for the globe
- `conjunctions` → updated close-approach warning cards
- `stats` → updated numbers for the header bar

**Why is this better than regular HTTP requests?**

With normal HTTP, the browser would have to ask the server "any updates?" 20 times per minute. Every request has overhead — it opens a connection, sends a header, waits, gets a response, closes the connection. For 2,000 satellite positions every 3 seconds, that is enormous waste.

With WebSocket, the connection is opened once and stays open. The server pushes updates the moment they are ready, with almost no overhead. Much faster and much more efficient.

---

## 🗄️ Caching Summary

The system has two layers of caching to ensure it always works even if external APIs fail:

| Data | Cache file | How long cached |
|---|---|---|
| Satellite TLE orbital data | `backend/tle_cache.txt` (2.7 MB) | 2 hours — auto-refreshed |
| Upcoming rocket launches | `backend/launch_cache.json` | 30 minutes — auto-refreshed |

---

## 🛠️ Full Tech Stack

| Part | Technology | Why |
|---|---|---|
| Backend language | **Python 3** | Readable, great scientific libraries |
| Web framework | **Flask** | Lightweight HTTP server |
| Real-time push | **Flask-SocketIO** | WebSocket streaming to browser |
| Orbital physics | **SGP4 algorithm** | Industry-standard satellite position math |
| Satellite data | **CelesTrak / NORAD** | Free, authoritative TLE source |
| Launch data | **Launch Library 2 API** | Real global launch schedule database |
| 3D rendering | **Three.js (WebGL)** | GPU-accelerated 3D in the browser |
| Frontend | **Vanilla JavaScript + CSS** | No framework dependency, fast load |
| Database | **SQLite** | User accounts, watchlists, preferences |

---

## 💬 Interview Q&A — Quick Answers

---

**Q: Why WebSockets instead of normal HTTP API calls?**

HTTP polling for 2,000 satellite positions 20 times a minute creates huge overhead — each request has a full connection lifecycle. WebSocket keeps one persistent connection open; the server just pushes updates the moment they are ready. Lower latency, lower CPU cost, scales much better.

---

**Q: How do you show 2,000+ satellites without the browser freezing?**

Three.js `InstancedMesh` — instead of creating 2,000 separate 3D objects, all satellite dots are batched into a single GPU draw call. The GPU renders all of them in one pass. This is why it stays at 60 FPS even with 2,000+ objects moving simultaneously.

---

**Q: How does the collision probability get calculated?**

It starts with a base probability derived from the 3D distance between the two objects (using the Haversine formula extended with altitude). That base score is then weighted by several factors: their relative orbital speeds, whether each object is an active controlled spacecraft or uncontrolled dead debris, the angle at which their orbits cross, and the density of tracked objects in that orbital region. The result is expressed as a log-scale percentage.

---

**Q: What if CelesTrak goes offline?**

The backend automatically falls back to `tle_cache.txt` — a local copy of the last successful download. The dashboard continues running fully with the cached satellite positions. An API status flag is set so the UI can display a "using cached data" notice if needed.

---

**Q: What is SGP4?**

SGP4 stands for Simplified General Perturbations model 4. It is the standard mathematical algorithm used by NORAD, ESA, and virtually every aerospace agency in the world to compute satellite positions from TLE data. You give it a TLE and a timestamp, it gives you back latitude, longitude, and altitude. It accounts for Earth's oblateness, atmospheric drag, solar pressure, and gravitational perturbations from the Moon and Sun.

---

**Q: What is a TLE?**

Two-Line Element set. A standardised two-line text format maintained by NORAD that encodes the orbital parameters of a space object at a specific point in time. It contains: object ID, epoch (the reference time), drag coefficient, inclination, right ascension, eccentricity, argument of perigee, mean anomaly, and mean motion (revolutions per day). From these numbers, SGP4 can extrapolate the object's position at any time.

---

## ▶️ How to Run the Project

```bash
# Terminal 1 — Start the backend API server
python backend/app.py

# Terminal 2 — Serve the frontend files
cd frontend
python -m http.server 8000

# Open in browser
http://localhost:8000
```

Backend runs on port **5000** (Flask + SocketIO).  
Frontend runs on port **8000** (static file server).  
The browser connects to both — loads the UI from 8000, gets live data from 5000.
