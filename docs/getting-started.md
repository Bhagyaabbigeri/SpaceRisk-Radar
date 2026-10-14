# Getting Started

This page walks you through running SpaceRisk Radar on your own machine. Follow every step in order.

## Prerequisites

| Requirement | Minimum version | How to check |
|---|---|---|
| Python | 3.10 | `python --version` |
| pip | bundled with Python | `pip --version` |
| Git | any | `git --version` |
| A modern browser | Chrome 90+, Firefox 88+, Edge 90+ | — |

No Node.js, no Docker, no database server — the app is a single Python process.

## Step 1 — Clone the repository

```bash
git clone https://github.com/Bhagyaabbigeri/SpaceRisk-Radar.git
cd SpaceRisk-Radar
```

## Step 2 — Create and activate a virtual environment

=== "Windows"

    ```bat
    python -m venv .venv
    .venv\Scripts\activate
    ```

=== "macOS / Linux"

    ```bash
    python -m venv .venv
    source .venv/bin/activate
    ```

Your prompt should now show `(.venv)` at the start.

## Step 3 — Install Python dependencies

```bash
pip install -r requirements.txt
```

This installs Flask, Flask-SocketIO, Eventlet, SGP4, and the other libraries listed in `requirements.txt`. It does **not** install MkDocs; those go in a separate file (see [Style Guide](style-guide.md#running-the-docs-site)).

## Step 4 — Start the server

```bash
python backend/app.py
```

You should see log lines like:

```
INFO  TLE background loader spawned.
INFO  Background TLE refresh thread spawned.
INFO  Socket.IO emitter thread spawned.
INFO  Alert monitoring scheduler spawned.
 * Running on http://0.0.0.0:5000
```

The server does three things at startup:

1. Loads TLE data from the local cache (`backend/tle_cache.txt`). If the cache is missing or older than 2 hours, it fetches fresh data from CelesTrak.
2. Starts a background thread that re-fetches TLEs every 10 minutes.
3. Starts a background thread that propagates satellite positions and pushes them to connected browsers every 3 seconds over WebSocket.

## Step 5 — Open the dashboard

Navigate to **[http://localhost:5000](http://localhost:5000)** in your browser.

The backend serves the frontend (HTML, JS, images) as static files from the same Python process. You do **not** need a separate web server for the frontend.

## What you should see

Within about 10 seconds of opening the page:

- A 3D Earth globe rotates slowly.
- Coloured dots appear on the globe — each dot is a tracked object.
- The HUD panels on the left and right fill in with live numbers (total objects, active conjunctions, average altitude).
- The conjunction list below the stats panel populates if any objects are within the screening threshold (default 500 km).

If the globe is empty after 30 seconds, open the browser console (`F12 → Console`) and look for WebSocket errors. The most common cause is a firewall blocking port 5000.

## Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| `ModuleNotFoundError: No module named 'flask'` | Virtual environment not activated | Run `.venv\Scripts\activate` (Windows) or `source .venv/bin/activate` |
| `Address already in use: 5000` | Another process is using port 5000 | `kill $(lsof -ti:5000)` or restart your machine |
| Globe loads but stays empty | CelesTrak fetch failed | Check your internet connection; the app will retry on the next 10-minute cycle |
