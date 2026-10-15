# 🛰️ SpaceRisk Radar — 2-Minute Project Overview (Interview Pitch)

> **A simple, conversational 2-minute script and cheat sheet for software engineering interviews at space tech and aerospace companies.**

---

## 🎙️ The 2-Minute Interview Pitch (Script)

Read or speak this naturally during your technical interview when asked: *"Can you give me an overview of your project?"*

> *"Earth orbit contains thousands of active spacecraft and tracked debris objects, so screening close approaches can help users assess possible risks.
>
> I built **SpaceRisk Radar** as an orbital collision-risk screening and visualization platform. It propagates up to 2,000 catalog objects per cycle with SGP4, screens close approaches, creates deterministic illustrative Kessler estimates, and visualizes the results on an interactive 3D globe.
>
> On the backend, I built the service using **Python, Flask, and Flask-SocketIO**. It checks its cached Two-Line Element (TLE) catalog from **CelesTrak** every 10 minutes, attempts a fetch when the cache is missing, has fewer than 100 objects, or is older than 2 hours, propagates up to 2,000 catalog entries using SGP4, and screens their pairwise 3D distances. The risk engine returns heuristic probability scores, and the server pushes telemetry to connected browsers every 3 seconds via **Socket.IO**.
>
> On the frontend, I designed a **Three.js 3D WebGL globe** HUD interface. It displays up to 2,000 catalog objects per cycle, orbital trajectories, conjunction lines, ground-station visibility, and orbital-density heatmaps. The project does not claim a fixed frame rate.
>
> Two additional features are its **Kessler Syndrome Cascade Simulator**, which uses deterministic formula-based illustrative estimates, and its **Ground Station Visibility Analyzer**, which computes line-of-sight visibility from five stations using a 10° minimum elevation mask.
>
> Finally, the platform includes **JWT-based user authentication**, customizable user watchlists, an alert notification dispatcher, and integrations with **Launch Library 2** to track upcoming rocket launches."*

---

## 💡 Simple Breakdown (What Each Part Means)

| Part | What You Are Telling The Interviewer | Why It Sounds Impressive |
| :--- | :--- | :--- |
| **1. The Problem** | Thousands of satellites and tracked debris objects make close-approach screening relevant to space situational awareness. | Demonstrates awareness of real aerospace & space situational awareness (SSA) challenges. |
| **2. The Solution** | SpaceRisk Radar brings recurring catalog propagation, heuristic risk screening, and 3D visualization into one dashboard. | Shows end-to-end software implementation across a backend and interactive frontend. |
| **3. The Backend Engine** | Flask + Flask-SocketIO backend using SGP4 on CelesTrak TLE data, screening up to 2,000 catalog entries per cycle and producing heuristic probability scores. | Shows a recurring data pipeline with orbital propagation, pairwise screening, and Socket.IO updates. |
| **4. The 3D Frontend** | Interactive Three.js WebGL globe displaying up to 2,000 catalog objects, orbits, heatmaps, and ground-station visibility. | Demonstrates end-to-end UI implementation with live telemetry. |
| **5. Deterministic Risk Estimates** | Formula-based illustrative Kessler cascade estimates and line-of-sight visibility analysis for five stations with a 10° elevation mask. | Describes the implemented screening and visualization features without implying machine learning or Monte Carlo modeling. |
| **6. User Accounts & Integrations** | JWT authentication, SQLite user watchlists/preferences, alert dispatching, and Launch Library 2 API integration. | Demonstrates account features and external API integration. |

---

## 🎯 Quick Cheat Sheet: Simple Definitions of Tech Terms Used

* **Two-Line Element (TLE)**: A standardized set consisting of a name line and two data lines containing orbital elements for a specific epoch.
* **SGP4 / SDP4 Algorithm**: Simplified General Perturbations models that estimate satellite positions from TLE data at a requested time.
* **Conjunction Screening**: The automated process of screening pairs among up to 2,000 propagated catalog objects against a configurable distance threshold. The dashboard slider ranges from 10 km to 2,000 km; the backend accepts values through 5,000 km.
* **Kessler Syndrome**: A dangerous scenario where space debris collisions create a chain reaction of more debris, rendering orbits unusable.
* **Flask & Flask-SocketIO**: A Python web framework and Socket.IO integration used to send telemetry updates to connected browsers without page refreshes.
* **Three.js**: A JavaScript 3D WebGL library used to render GPU-accelerated graphics (like our interactive 3D Earth, satellites, and orbit trajectories) inside a web browser.
* **Ground Station Elevation Masking**: Line-of-sight math that estimates whether a satellite is above a station's configured minimum elevation angle.

---

## ❓ Simple Answers to Quick Follow-Up Questions

### Q1: "Why did you use Flask-SocketIO instead of standard HTTP REST polling for live telemetry?"
> *"Socket.IO lets the server push updates to connected clients every 3 seconds instead of requiring a separate browser request for each update. The app sends propagated object data and analysis results to the dashboard."*

### Q2: "How do you display up to 2,000 catalog objects on the 3D globe?"
> *"The app caps the propagated catalog at 2,000 objects per cycle. The current globe creates individual Three.js mesh objects, so rendering speed depends on the device and is not specified as a fixed frame rate."*

### Q3: "How does the Kessler Syndrome simulator work?"
> *"The Kessler module takes up to five closest conjunctions and uses deterministic formulas to estimate hypothetical cloud size, fragment count, and secondary-risk scores. It does not model object mass, random fragment trajectories, or time-evolving debris propagation."*

### Q4: "What happens if CelesTrak or external data sources are offline?"
> *"The app stores TLE data locally and can use the saved file when a CelesTrak fetch is unavailable. Propagation then depends on the TLE data available in that file."*
