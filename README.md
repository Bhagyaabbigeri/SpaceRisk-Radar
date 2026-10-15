<p align="center">
  <img src="frontend/SpaceRisk_Radar_live_Dashboard.png" alt="SpaceRisk Radar Dashboard" width="900"/>
</p>

<h1 align="center">🛰️ SpaceRisk Radar</h1>
<h3 align="center">Orbital Collision-Risk Screening & Visualization Platform</h3>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white" />
  <img src="https://img.shields.io/badge/Flask-2.2+-000000?style=for-the-badge&logo=flask&logoColor=white" />
  <img src="https://img.shields.io/badge/Three.js-r150+-000000?style=for-the-badge&logo=three.js&logoColor=white" />
  <img src="https://img.shields.io/badge/SGP4-Orbital_Mechanics-FF6B35?style=for-the-badge" />
  <img src="https://img.shields.io/badge/License-MIT-green?style=for-the-badge" />
</p>

<p align="center">
  A real-time space situational awareness platform that propagates satellite orbits using SGP4/SDP4 algorithms, screens for conjunction threats, estimates illustrative Kessler syndrome debris risks, and visualizes the orbital environment on an interactive 3D globe.
</p>

<p align="center">
  <strong>GitHub:</strong> <a href="https://github.com/Bhagyaabbigeri/SpaceRisk-Radar">https://github.com/Bhagyaabbigeri/SpaceRisk-Radar</a>
</p>

## 📋 Table of Contents

- [Project Overview](#-project-overview)
- [Problem Statement](#-problem-statement)
- [Key Features](#-key-features)
- [System Architecture](#-system-architecture)
- [Technology Stack](#-technology-stack)
- [Project Structure](#-project-structure)
- [Installation Guide](#-installation-guide)
- [Running the Application](#-running-the-application)
- [API Endpoints](#-api-endpoints)
- [Data Sources](#-data-sources)
- [Orbital Collision-Risk Screening Module](#-orbital-collision-risk-screening-module)
- [Kessler Syndrome Risk Analysis](#-kessler-syndrome-risk-analysis)
- [Ground Station Visibility Analysis](#-ground-station-visibility-analysis)
- [Orbital Heatmap Visualization](#-orbital-heatmap-visualization)
- [Upcoming Launch Tracking](#-upcoming-launch-tracking)
- [Screenshots](#-screenshots)
- [Future Enhancements](#-future-enhancements)
- [Research & Scientific Background](#-research--scientific-background)
- [Performance & Scalability](#-performance--scalability)
- [Limitations](#-limitations)
- [Contributing Guidelines](#-contributing-guidelines)
- [License](#-license)
- [Author](#-author)

---

## 🌍 Project Overview

**SpaceRisk Radar** is a comprehensive space situational awareness (SSA) platform designed to monitor, screen for, and visualize orbital conjunction risks in real time. The platform ingests Two-Line Element (TLE) data from CelesTrak, propagates satellite positions using the SGP4/SDP4 orbital mechanics model, and performs proximity screening to identify potential conjunction events between space objects.

The system features a cinematic **3D globe visualization** built with Three.js that renders satellite positions, orbital trajectories, conjunction threat lines, ground station markers, orbital congestion heatmaps, and illustrative debris-cloud estimates — all updated in real time via WebSocket connections.

---

## 🎯 Problem Statement

With over **10,000+ active satellites** and **36,000+ tracked debris objects** orbiting Earth, the risk of orbital collisions has never been higher. The 2009 Iridium-Cosmos collision and the 2021 Russian ASAT test demonstrated how a single event can generate thousands of debris fragments, threatening the long-term sustainability of space operations.

**SpaceRisk Radar** addresses these challenges by providing:

- **Real-time conjunction screening** for collision avoidance decision-making
- **Kessler syndrome simulation** to assess cascading debris risks
- **Accessible visualization** that makes orbital mechanics data understandable
- **Open-source tooling** for researchers, educators, and space enthusiasts

---

## ✨ Key Features

| Feature | Description |
|---|---|
| 🌐 **3D Globe Visualization** | Interactive Three.js globe rendering up to 2,000 TLE objects per live cycle with orbital trajectories |
| ⚠️ **Conjunction Detection** | Automated proximity screening with configurable threshold (10–5000 km) |
| 🔴 **Multi-Tier Risk Assessment** | CRITICAL / HIGH / MEDIUM / LOW threat classification with collision probability |
| 💥 **Kessler Syndrome Simulation** | Deterministic formula-based debris estimate with chain-probability analysis |
| 📡 **Ground Station Visibility** | Line-of-sight analysis for 5 stations: White Sands (USA), Goldstone DSN (USA), Madrid DSN (Spain), Canberra DSN (Australia), and Sriharikota (India) |
| 🗺️ **Orbital Heatmap** | Congestion density visualization binned by lat/lon grid cells |
| 🚀 **Launch Tracking** | Upcoming launch schedule from Launch Library 2 API with countdown values |
| 🔄 **Real-Time Updates** | Socket.IO WebSocket push every 3 seconds for live telemetry |
| 🔍 **Satellite Search** | Normalized substring search across the TLE catalog with auto-complete results |
| ⭐ **Favorites & Watchlist** | Bookmark satellites for quick access with persistent local storage |
| 🔐 **User Authentication** | JWT-based auth with SQLite user profiles, preferences, and alert settings |
| 📊 **Maneuver Predictions** | ISS/Hubble scenario inputs with lightweight trajectory previews |
| ⏱️ **Historical Playback** | Time-slider to propagate orbits over a 24-hour lookback window |
| 📱 **Responsive Design** | Glassmorphism HUD interface optimized for desktop and tablet |

---

## 🏗️ System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        CLIENT (Browser)                         │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────────┐   │
│  │ Three.js │  │  HUD UI  │  │ Socket.IO│  │  REST Client │   │
│  │  Globe   │  │  Panels  │  │  Client  │  │  (Fetch API) │   │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └──────┬───────┘   │
│       └──────────────┴────────────┬┴───────────────┘           │
└───────────────────────────────────┼─────────────────────────────┘
                                    │ HTTP / WebSocket
┌───────────────────────────────────┼─────────────────────────────┐
│                     BACKEND (Flask + SocketIO)                   │
│  ┌────────────────┐  ┌─────────────────┐  ┌──────────────────┐ │
│  │  TLE Fetcher   │  │ Orbit Calculator│  │   Risk Engine    │ │
│  │  (CelesTrak)   │  │  (SGP4/SDP4)    │  │  (Conjunction)   │ │
│  └───────┬────────┘  └───────┬─────────┘  └────────┬─────────┘ │
│          │                   │                      │           │
│  ┌───────┴───────┐  ┌───────┴─────────┐  ┌────────┴─────────┐ │
│  │ Ground Station│  │ Kessler Cascade │  │  Heatmap Engine  │ │
│  │  Visibility   │  │   Simulator     │  │  (Density Grid)  │ │
│  └───────────────┘  └─────────────────┘  └──────────────────┘ │
│  ┌───────────────┐  ┌─────────────────┐  ┌──────────────────┐ │
│  │ Launch Tracker│  │Maneuver Predict │  │  Auth Service    │ │
│  │ (LL2 API)     │  │ (Drag Decay)    │  │  (JWT + SQLite)  │ │
│  └───────────────┘  └─────────────────┘  └──────────────────┘ │
│  ┌───────────────┐  ┌─────────────────┐  ┌──────────────────┐ │
│  │  Alert System │  │  Cache Layer    │  │  API v1 Router   │ │
│  │  (Dispatcher) │  │  (In-Memory)    │  │  (Blueprint)     │ │
│  └───────────────┘  └─────────────────┘  └──────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🛠️ Technology Stack

### Backend
| Technology | Purpose |
|---|---|
| **Python 3.10+** | Core backend language |
| **Flask 2.2+** | Lightweight REST API framework |
| **Flask-SocketIO** | Real-time WebSocket push for live telemetry |
| **SGP4** | Satellite orbit propagation (NORAD TLE standard) |
| **Flask-CORS** | Cross-origin resource sharing for frontend integration |
| **PyJWT** | JSON Web Token authentication |
| **SQLite** | Lightweight embedded database for user data |
| **Werkzeug** | Password hashing and WSGI utilities |

### Frontend
| Technology | Purpose |
|---|---|
| **HTML5 / CSS3 / JavaScript** | Core web technologies |
| **Three.js** | 3D WebGL globe rendering |
| **Socket.IO Client** | Real-time data streaming |
| **Ionicons** | Icon library for HUD interface |
| **Google Fonts** | Orbitron + Rajdhani typography |

### External Data Sources
| Source | Data |
|---|---|
| **CelesTrak** | Two-Line Element (TLE) satellite catalog |
| **Launch Library 2** | Upcoming launch schedule data |

---

## 📁 Project Structure

```
SpaceRisk-Radar/
├── backend/
│   ├── app.py                  # Main Flask application & Socket.IO server
│   ├── tle_fetcher.py          # TLE data fetcher from CelesTrak with caching
│   ├── orbit_calculator.py     # SGP4/SDP4 orbit propagation engine
│   ├── risk_engine.py          # Conjunction screening & collision probability
│   ├── ground_station.py       # Ground station visibility analysis
│   ├── heatmap.py              # Orbital congestion heatmap computation
│   ├── kessler.py              # Kessler syndrome cascade simulation
│   ├── launches.py             # Upcoming launch data from Launch Library 2
│   ├── maneuvers.py            # Maneuver prediction & orbit decay modeling
│   ├── alerts.py               # Alert dispatcher & scheduling system
│   ├── auth_service.py         # JWT authentication & user management
│   ├── api_v1.py               # Versioned API v1 blueprint router
│   ├── cache_layer.py          # In-memory caching layer with TTL
│   └── openapi_spec.py         # OpenAPI 3.0 specification generator
│
├── frontend/
│   ├── index.html              # Main HUD dashboard (glassmorphism UI)
│   ├── globe.js                # Three.js 3D globe renderer
│   ├── ui.js                   # UI logic, filters, search, and telemetry
│   ├── earth_cyber_texture.png # Custom globe texture
│   ├── screenshot.png          # Application screenshot
│   └── vendor/
│       ├── socket.io.min.js    # Socket.IO client library
│       ├── socket.io.local.js  # Socket.IO local fallback
│       └── ionicons.local.js   # Ionicons local fallback
│
├── tools/
│   ├── check_frontend.py       # Frontend health-check utility
│   ├── check_objects.py        # Object propagation verification
│   ├── inspect_app.py          # App inspection utility
│   ├── run_search_nisar_local.py # Search integration test
│   ├── search_nisar.py         # NISAR satellite search test
│   └── test_search_urls.py     # URL search endpoint tests
│
├── requirements.txt            # Python dependencies
├── .gitignore                  # Git ignore rules
└── README.md                   # This file
```

---

## 🚀 Installation Guide

### Prerequisites

- **Python 3.10+** — [Download Python](https://www.python.org/downloads/)
- **pip** — Python package manager (included with Python)
- **Git** — [Download Git](https://git-scm.com/downloads)
- **Modern web browser** — Chrome, Firefox, or Edge recommended

### Backend Setup

```bash
# 1. Clone the repository
git clone https://github.com/Bhagyaabbigeri/SpaceRisk-Radar.git
cd SpaceRisk-Radar

# 2. Create a virtual environment
python -m venv .venv

# 3. Activate the virtual environment
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

# 4. Install Python dependencies
pip install -r requirements.txt
```

### Frontend Setup

The frontend is a static HTML/CSS/JS application — **no build step required**.

The Three.js library is loaded from a CDN in `index.html`. Socket.IO and Ionicons have local vendor fallbacks included.

---

## ▶️ Running the Application

### Step 1: Start the Application

```bash
# From the project root directory
python backend/app.py
```

The Flask app serves the frontend and starts the backend services with:
- REST API endpoints for satellite data, conjunctions, and stats
- Socket.IO WebSocket server for real-time push updates
- Background threads for TLE refresh (every 10 minutes) and live object emission (every 3 seconds)

### Step 2: Frontend Serving

The Flask app serves the frontend directly; no separate frontend server is required.

### Step 3: Open the Dashboard

Navigate to **`http://localhost:5000`** in your browser.

> **Note:** Port 5000 serves the frontend, API, and Socket.IO streams from Flask. No separate frontend server or port 8000 is used.

---

## 📡 API Endpoints

### Core Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/objects` | Propagated satellite positions (lat, lon, alt, speed) |
| `GET` | `/api/objects?at=<ISO-8601>` | Historical/future orbit propagation at specific time |
| `GET` | `/api/satellite?name=<name>` | Detailed telemetry for a single satellite |
| `GET` | `/api/search?q=<query>` | Normalized substring search across the TLE catalog (max 10 results) |
| `GET` | `/api/conjunctions` | Active conjunction threat list with risk levels |
| `GET` | `/api/conjunctions?threshold=<km>` | Custom proximity threshold (default: 500 km) |
| `GET` | `/api/stats` | Statistics for the propagated object set |

### Advanced Analysis Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/ground-visibility` | Ground station line-of-sight visibility data |
| `GET` | `/api/heatmap` | Orbital congestion density grid |
| `GET` | `/api/debris-risk` | Kessler syndrome cascade simulation results |
| `GET` | `/api/maneuvers` | ISS/Hubble maneuver scenario inputs and trajectory previews |
| `GET` | `/api/launches` | Upcoming launch schedule (from Launch Library 2) |

### Authentication Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/v1/auth/signup` | Create new user account |
| `POST` | `/api/v1/auth/login` | Authenticate and receive JWT token |
| `POST` | `/api/v1/auth/logout` | Log out (discard bearer token client-side; requires auth) |
| `GET` | `/api/v1/auth/me` | Get current user (requires auth) |
| `PATCH` | `/api/v1/profile` | Update user profile (requires auth) |
| `GET` | `/api/v1/preferences` | Get user preferences (requires auth) |
| `PUT` | `/api/v1/preferences` | Update user preferences and alert settings (requires auth) |
| `POST` | `/api/v1/watched-satellites` | Add a watched satellite (requires auth) |
| `DELETE` | `/api/v1/watched-satellites/<path:name>` | Remove a watched satellite (requires auth) |

### WebSocket Events

| Event | Direction | Description |
|---|---|---|
| `objects` | Server → Client | Live satellite positions (every 3s) |
| `conjunctions` | Server → Client | Real-time conjunction alerts |
| `stats` | Server → Client | Statistics for the propagated object set |
| `ground_visibility` | Server → Client | Ground station visibility data |
| `heatmap` | Server → Client | Orbital congestion heatmap |
| `debris_risk` | Server → Client | Kessler cascade risk updates |
| `maneuvers` | Server → Client | Maneuver predictions |
| `set_threshold` | Client → Server | Update conjunction screening distance |

---

## 📊 Data Sources

### Two-Line Element Sets (TLE)

SpaceRisk Radar fetches satellite orbital elements from **[CelesTrak](https://celestrak.org/)**, maintained by Dr. T.S. Kelso. TLE data includes:

- CelesTrak TLE catalog (object count varies)
- Keplerian orbital elements: inclination, RAAN, eccentricity, argument of perigee, mean anomaly, mean motion
- NORAD catalog numbers for cross-referencing with Space-Track.org
- Element epoch included with propagated object metadata

The backend implements a **2-hour local file cache** (`tle_cache.txt`) to reduce repeated CelesTrak requests, with a background refresh check every 10 minutes.

### Launch Data

Upcoming launch information is sourced from the **[Launch Library 2 API](https://thespacedevs.com/)** with a 30-minute local cache and a static placeholder fallback when the API is unavailable.

---

## ⚠️ Orbital Collision-Risk Screening Module

The conjunction screening engine (`risk_engine.py`) implements a multi-stage collision assessment pipeline:

### Stage 1: Proximity Screening
- Computes pairwise distances between all propagated satellite positions
- Filters pairs within the configurable screening threshold (default: 500 km)
- Uses a 3D distance estimate combining surface haversine distance and altitude difference

### Stage 2: Risk Classification
| Level | Probability threshold | Color | Description |
|---|---|---|---|
| **CRITICAL** | ≥ 0.001 | 🔴 Red | Highest heuristic score — review event details |
| **HIGH** | ≥ 0.0001 | 🟠 Orange | Elevated heuristic score — close monitoring recommended |
| **MEDIUM** | ≥ 0.000001 | 🟡 Yellow | Moderate heuristic score — routine tracking |
| **LOW** | < 0.000001 | 🔵 Blue | Lowest heuristic score — logged for awareness |

### Stage 3: Collision Probability
- Heuristic probability score using 3D distance, orbit class, average object speed, debris indicators in operator/country/name fields, and inclination
- Risk factors are derived from proximity, orbit class, average speed, debris indicators, and polar inclinations
- Heuristic evasion text is selected from debris flags and object names; it is not an orbit-optimized maneuver plan

---

## 💥 Kessler Syndrome Risk Analysis

The Kessler module (`kessler.py`) estimates an illustrative cascading-debris scenario:

- **Deterministic, formula-based estimate** of debris generation from selected conjunction events
- **Debris-count estimate** based on miss distance
- **Chain-probability estimate** for nearby objects within a fixed-radius cloud
- **Debris-cloud visualization** using estimated centers and fixed-radius regions
- **Cumulative chain-probability sum** across up to five selected conjunction events

The estimate uses:
- Miss distance to calculate primary probability and estimated debris count
- The midpoint of conjunction-object positions as the estimated cloud center
- Nearby object positions within a fixed radius to estimate chain probabilities
- A fixed-radius cloud rather than fragment dispersion cone modeling

---

## 📡 Ground Station Visibility Analysis

The ground station module (`ground_station.py`) computes real-time line-of-sight visibility between satellites and five defined stations:

**Included Ground Stations:**
- White Sands (USA), Goldstone DSN (USA)
- Madrid DSN (Spain), Canberra DSN (Australia)
- Sriharikota (India)

**Analysis Features:**
- Elevation angle masking (minimum 10° above horizon)
- Visibility-duration approximation based on elevation and altitude
- Ground-station markers rendered on the 3D globe
- Best visible station selected by elevation angle

---

## 🗺️ Orbital Heatmap Visualization

The heatmap engine (`heatmap.py`) generates an orbital congestion density map:

- **Grid-based binning** of satellite positions across latitude/longitude cells
- **Altitude band segmentation** (LEO / MEO / GEO / HEO)
- **Density normalization** against the highest-density cell, with risk scores used for heatmap coloring
- **Real-time updates** as satellite positions are re-propagated
- Identification of **high-density grid cells** ranked by satellite count

---

## 🚀 Upcoming Launch Tracking

The launch tracker (`launches.py`) provides visibility into the near-term launch manifest:

- **Live data** from Launch Library 2 API (thespacedevs.com)
- **Launch countdown values** displayed on the HUD interface
- **Launch mission and vehicle identification**
- **Pad location mapping** with geographic coordinates
- **Static placeholder fallback** when Launch Library 2 is unavailable

---

## 📸 Screenshots

<p align="center">
  <img src="frontend/screenshot.png" alt="SpaceRisk Radar - 3D Globe Dashboard" width="900"/>
</p>

### 🛰️ Interactive Gallery

<p align="center">
  <img src="screenshots/SpaceRisk-Rader1.png" alt="Global Orbital Network" width="900"/>
  <br/>
  <b>Global Orbital Network</b>
</p>

<p align="center">
  <img src="screenshots/SpaceRisk-Rader2.png" alt="Real-time Telemetry HUD" width="900"/>
  <br/>
  <b>Real-time Telemetry HUD</b>
</p>

<p align="center">
  <img src="screenshots/SpaceRisk-Rader3.png" alt="Polar Coverage Analysis" width="900"/>
  <br/>
  <b>Polar Coverage Analysis</b>
</p>

<p align="center">
  <img src="screenshots/SpaceRisk-Rader4.png" alt="Conjunction Threat Detection" width="900"/>
  <br/>
  <b>Conjunction Threat Detection</b>
</p>

<p align="center">
  <img src="screenshots/SpaceRisk-Rader5.png" alt="Account & Control Panel" width="900"/>
  <br/>
  <b>Account & Control Panel</b>
</p>

<p align="center">
  <img src="screenshots/SpaceRisk-Rader6.png" alt="Deep Space Monitoring" width="900"/>
  <br/>
  <b>Deep Space Monitoring</b>
</p>

<p align="center">
  <img src="screenshots/SpaceRisk-Rader7.png" alt="Mission Replay Timeline" width="900"/>
  <br/>
  <b>Mission Replay Timeline</b>
</p>

<p align="center">
  <img src="screenshots/SpaceRisk-Rader8.png" alt="Satellite Tracking Dashboard" width="900"/>
  <br/>
  <b>Satellite Tracking Dashboard</b>
</p>

<p align="center">
  <img src="screenshots/SpaceRisk-Rader9.png" alt="Operational HUD View" width="900"/>
  <br/>
  <b>Operational HUD View</b>
</p>

<p align="center"><em>SpaceRisk Radar dashboard showing real-time satellite tracking, conjunction threat detection, and orbital telemetry HUD panels</em></p>

---

## 🔮 Future Enhancements

- [ ] **Machine Learning Conjunction Prediction** — LSTM-based time-series forecasting for miss distance trends
- [ ] **Space-Track.org Integration** — Official USSPACECOM conjunction data messages (CDM)
- [ ] **Starlink Constellation Tracker** — Dedicated mega-constellation monitoring module
- [ ] **Orbital Debris Remediation Scoring** — Active debris removal (ADR) priority ranking
- [ ] **Multi-User Collaboration** — Shared watchlists and team alert channels
- [ ] **Mobile PWA** — Progressive web app for mobile field deployment
- [ ] **Docker Containerization** — One-command deployment with Docker Compose
- [ ] **PostgreSQL Migration** — Production-grade database for user management
- [ ] **SMS and additional alert integrations** — Automated conjunction alert notifications
- [ ] **TLE Accuracy Decay Monitoring** — Epoch freshness tracking and prediction confidence scoring

---

## 📚 Research & Scientific Background

SpaceRisk Radar builds on established methodologies from orbital mechanics and space surveillance:

### Orbital Propagation — SGP4/SDP4
The Simplified General Perturbations (SGP4) model, developed by the NORAD/USSPACECOM, propagates satellite positions from Two-Line Element sets. The implementation accounts for:
- Earth's oblateness (J2, J3, J4 zonal harmonics)
- Atmospheric drag effects (for LEO objects)
- Solar and lunar gravitational perturbations (SDP4 for deep-space objects)
- Secular and periodic variations in orbital elements

**Reference:** Vallado, D.A., Crawford, P., Hujsak, R., Kelso, T.S. (2006). *Revisiting Spacetrack Report #3*. AIAA/AAS Astrodynamics Specialist Conference.

### Conjunction Assessment
The proximity screening methodology follows operational practices from:
- **NASA Conjunction Assessment (CA)** program
- **ESA Space Debris Office** collision avoidance protocols
- **JSpOC (now CSpOC)** screening volume definitions

### Kessler Syndrome
The cascading collision model is inspired by:
- Kessler, D.J., Cour-Palais, B.G. (1978). *Collision frequency of artificial satellites: The creation of a debris belt*. Journal of Geophysical Research, 83(A6), 2637-2646.
- Liou, J.-C., Johnson, N.L. (2006). *Risks in Space from Orbiting Debris*. Science, 311(5759), 340-341.

---

## ⚡ Performance & Scalability

| Metric | Value |
|---|---|
| **Catalog Size** | Up to 2,000 TLE catalog objects per live cycle |
| **Update Frequency** | 3-second Socket.IO push cycle |
| **TLE Refresh** | Every 10 minutes (2-hour file cache) |
| **API Response Time** | < 500ms for cached endpoints |
| **Cache TTL** | 10 seconds–30 minutes (endpoint-dependent) |
| **WebSocket Protocol** | Socket.IO with Eventlet async mode |
| **Browser Target** | Chrome 90+, Firefox 88+, Edge 90+ |
| **Propagation Engine** | SGP4 via `python-sgp4` (compiled C extensions) |

### Optimization Strategies
- **Redis-backed caching with in-memory fallback** and TTL-based expiration (`cache_layer.py`)
- **Background worker threads** for TLE refresh and Socket.IO emission
- **Propagation limit** (2,000 catalog objects) to bound CPU usage
- **Client-side filtering** to limit rendered objects
- **Bounded advanced overlays** (heatmap, debris risk, and other analysis computed during the live worker cycle)

---

## ⚠️ Limitations

- TLE-based propagation can become less accurate as an element set's epoch gets older; the app exposes the epoch but does not calculate age-based confidence.
- Orbit states use SGP4 propagation rather than high-fidelity numerical integration.
- Collision probability is a heuristic score, not an operational collision probability.
- At most 2,000 catalog TLEs are propagated per live cycle; a separate synthetic object is then injected.
- When catalog objects are available, the runtime injects `TEST_DEBRIS_X`; it is synthetic and is not real debris.
- The Kessler module is an illustrative formula-based estimate, not a physical fragment simulation.

For details, see [docs/limitations.md](docs/limitations.md).

---

## 🤝 Contributing Guidelines

Contributions are welcome! Please follow these steps:

1. **Fork** the repository
2. **Create** a feature branch:
   ```bash
   git checkout -b feature/your-feature-name
   ```
3. **Commit** your changes with meaningful messages:
   ```bash
   git commit -m "feat: add new orbital decay visualization"
   ```
4. **Push** to your fork:
   ```bash
   git push origin feature/your-feature-name
   ```
5. **Open** a Pull Request against `main`

### Commit Message Convention
- `feat:` — New feature
- `fix:` — Bug fix
- `docs:` — Documentation changes
- `refactor:` — Code restructuring
- `test:` — Test additions/modifications
- `chore:` — Build process or auxiliary tool changes

---

## 📄 License

This project is licensed under the **MIT License** — see the [LICENSE](LICENSE) file for details.

```
MIT License

Copyright (c) 2025 Bhagyaabbigeri

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

---

## 👤 Author

**Bhagyashree Reddy**

- GitHub: [@Bhagyaabbigeri](https://github.com/Bhagyaabbigeri)
- Project: [SpaceRisk-Radar](https://github.com/Bhagyaabbigeri/SpaceRisk-Radar)

---

<p align="center">
  <strong>🛰️ Protecting the orbital commons — one conjunction at a time.</strong>
</p>
