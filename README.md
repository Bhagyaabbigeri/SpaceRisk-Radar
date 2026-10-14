<p align="center">
  <img src="frontend/SpaceRisk_Radar_live_Dashboard.png" alt="SpaceRisk Radar live dashboard showing satellites on a 3D globe with HUD telemetry panels" width="900"/>
</p>

<h1 align="center">🛰️ SpaceRisk Radar</h1>
<h3 align="center">Real-Time Orbital Collision Risk &amp; Space Debris Monitoring</h3>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white" />
  <img src="https://img.shields.io/badge/Flask-3.1-000000?style=for-the-badge&logo=flask&logoColor=white" />
  <img src="https://img.shields.io/badge/Three.js-WebGL_Globe-000000?style=for-the-badge&logo=three.js&logoColor=white" />
  <img src="https://img.shields.io/badge/SGP4-Orbit_Propagation-FF6B35?style=for-the-badge" />
  <img src="https://img.shields.io/badge/License-MIT-green?style=for-the-badge" />
</p>

SpaceRisk Radar is a real-time space situational awareness platform. It fetches satellite orbital elements (TLEs) from CelesTrak every two hours, propagates up to 2,000 objects using the SGP4 model, screens every pair for close approaches, and streams the results to an interactive 3D globe in your browser via Socket.IO WebSocket — updated every 3 seconds.

SpaceRisk Radar runs locally. Follow the Getting Started guide to run it on your own machine.

**[📖 Documentation](https://bhagyaabbigeri.github.io/SpaceRisk-Radar/) &nbsp;|&nbsp; [GitHub](https://github.com/Bhagyaabbigeri/SpaceRisk-Radar)**

---

## Quick start

```bash
git clone https://github.com/Bhagyaabbigeri/SpaceRisk-Radar.git
cd SpaceRisk-Radar
python -m venv .venv && .venv\Scripts\activate   # Windows
# source .venv/bin/activate                       # macOS/Linux
pip install -r requirements.txt
python backend/app.py
```

Open **http://localhost:5000** in your browser. The backend serves the frontend from the same process — no separate frontend server needed.

See [Getting Started](https://bhagyaabbigeri.github.io/SpaceRisk-Radar/getting-started/) for the full walkthrough.

---

## Features

| Feature | Detail |
|---|---|
| 3D globe | Three.js WebGL, up to 2,000 live objects |
| Conjunction detection | Configurable threshold 10–5,000 km (default 500 km) |
| Risk scoring | Heuristic log-linear score — CRITICAL / HIGH / MEDIUM / LOW |
| Kessler simulation | Deterministic cascade model seeded by the closest 5 conjunctions |
| Ground visibility | 5 stations: White Sands, Goldstone DSN, Madrid DSN, Canberra DSN, Sriharikota |
| Orbital heatmap | Lat/lon density grid by altitude band |
| Historical replay | `?at=<ISO-8601>` propagates all orbits to any past or future epoch |
| Launch tracking | Upcoming launches from Launch Library 2 API |
| Auth | JWT, SQLite — sign up, log in, save a watchlist |
| API | REST + WebSocket; versioned routes under `/api/v1/` |

---

## Running the app

The app runs as a single Flask process. The frontend is served as static files from the same process — no separate web server is needed.

```bash
python backend/app.py
```

Flask-SocketIO uses Eventlet in async mode. Open **http://localhost:5000** when the server is ready.

---

## Architecture

```
CelesTrak TLEs ──► tle_fetcher.py ──► orbit_calculator.py (SGP4)
                                              │
                          ┌───────────────────┼───────────────────┐
                    risk_engine.py      ground_station.py     heatmap.py
                    (conjunctions)      (visibility)          (density)
                          │
                    kessler.py · maneuvers.py · launches.py
                          │
                    app.py Socket.IO emitter (every 3 s)
                          │
                    Browser · Three.js globe · HUD panels
```

---

## Docs site

The full technical documentation is at **https://bhagyaabbigeri.github.io/SpaceRisk-Radar/**

Built with [MkDocs Material](https://squidfunk.github.io/mkdocs-material/). To run locally:

```bash
pip install -r docs-requirements.txt
mkdocs serve
```

---

## Known facts and caveats

- **Collision probability** is a heuristic score derived from distance and orbital parameters. It does not use a covariance matrix. Do not use these numbers for operational manoeuvre decisions.
- **Propagation cap**: Only the first 2,000 TLEs in the catalog are propagated per cycle.
- **TEST_DEBRIS_X** is a synthetic object always injected near the first catalog entry. It is not real.
- **Screenshot filenames** in `screenshots/` are spelled "Rader" (a known typo in the directory). The project name is "Radar".
- **Ground stations**: 5 stations are defined in code (not 12 as stated in the original README).
- **Async mode**: Eventlet (not threading). See `app.py` line 44.

---

## License

MIT License — see [LICENSE](LICENSE).

## Author

**Bhagyashree Reddy**  
GitHub: [@Bhagyaabbigeri](https://github.com/Bhagyaabbigeri)  
Project: [SpaceRisk-Radar](https://github.com/Bhagyaabbigeri/SpaceRisk-Radar)

---

<p align="center"><strong>🛰️ Protecting the orbital commons — one conjunction at a time.</strong></p>
