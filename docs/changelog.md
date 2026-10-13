# Changelog

All notable changes to SpaceRisk Radar are documented here. This file follows the [Keep a Changelog](https://keepachangelog.com/en/1.0.0/) format.

---

## [Unreleased]

### Added

- MkDocs Material documentation site (`mkdocs.yml`, `docs-requirements.txt`)
- GitHub Actions workflow for automated docs deployment to GitHub Pages (`.github/workflows/docs.yml`)
- Documentation pages: index, getting-started, user-guide, concepts, how-it-works, limitations, api-reference, style-guide, blog
- Screenshots copied to `docs/assets/` for documentation use

---

## [1.0.0] — Initial release

### Added

- Real-time satellite tracking via CelesTrak TLE catalog
- SGP4 orbit propagation using `python-sgp4`
- Conjunction screening with configurable distance threshold (10–5000 km)
- Heuristic collision probability scoring (`risk_engine.py`)
- Kessler cascade simulation (`kessler.py`)
- Ground station visibility for 5 stations: White Sands, Goldstone DSN, Madrid DSN, Canberra DSN, Sriharikota
- Orbital congestion heatmap
- Upcoming launch tracking from Launch Library 2
- JWT-based user authentication with SQLite storage
- Watched-satellite watchlist (per-user, server-side)
- Socket.IO WebSocket push every 3 seconds
- Three.js 3D globe frontend
- Historical orbit replay via `?at=<ISO-8601>` query parameter
- REST API with versioned `/api/v1/` routes
- OpenAPI 3.0 spec at `/api/v1/openapi.json`
- Swagger UI at `/api/v1/docs`
- Gunicorn + Eventlet production deployment on Render
