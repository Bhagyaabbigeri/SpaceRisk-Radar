# 🛰️ SpaceRisk Radar — 2-Minute Project Overview (Interview Pitch)

> **A simple, conversational 2-minute script and cheat sheet for software engineering interviews at space tech and aerospace companies.**

---

## 🎙️ The 2-Minute Interview Pitch (Script)

Read or speak this naturally during your technical interview when asked: *"Can you give me an overview of your project?"*

> *"With over 10,000 active satellites and more than 36,000 tracked space debris fragments in Low Earth Orbit, space agencies and satellite operators face a critical challenge: predicting collisions before they happen and avoiding catastrophic debris chain reactions.
>
> I built **SpaceRisk Radar** as a real-time Space Situational Awareness (SSA) and orbital collision prediction platform. It monitors satellite trajectories, detects close approach threats (conjunctions), simulates Kessler syndrome debris cascades, and visualizes everything on an interactive 3D globe.
>
> On the backend, I built the service using **Python, Flask, and Flask-SocketIO**. The system continuously ingests live Two-Line Element (TLE) orbital data from **CelesTrak**, uses the **SGP4/SDP4 orbital mechanics algorithm** to propagate satellite positions in real time, and runs a custom **proximity screening engine** that calculates distance matrices and collision probabilities across thousands of objects, pushing live telemetry updates to connected browsers every 3 seconds via **WebSockets**.
>
> On the frontend, I designed a high-performance **Three.js 3D WebGL globe** HUD interface. It renders over 2,000 satellites, dynamic orbit trajectories, threat lines, ground station visibility cones, and orbital density heatmaps at a smooth **60 frames per second**.
>
> Two key advanced features of the platform are its **Kessler Syndrome Cascade Simulator**, which uses Monte Carlo modeling to analyze how a collision would trigger chain-reaction debris clouds, and its **Ground Station Visibility Analyzer**, which performs line-of-sight elevation masking across 12 global tracking stations.
>
> Finally, the platform includes **JWT-based user authentication**, customizable user watchlists, an alert notification dispatcher, and integrations with **Launch Library 2** to track upcoming rocket launches."*

---

## 💡 Simple Breakdown (What Each Part Means)

| Part | What You Are Telling The Interviewer | Why It Sounds Impressive |
| :--- | :--- | :--- |
| **1. The Problem** | 10k+ satellites & 36k+ debris pieces create constant collision risks that could destroy space infrastructure. | Demonstrates strong domain awareness of real aerospace & space situational awareness (SSA) challenges. |
| **2. The Solution** | SpaceRisk Radar brings real-time tracking, risk screening, and 3D visualization into one central dashboard. | Shows product engineering thinking and ability to build end-to-end mission-critical software. |
| **3. The Backend Engine** | Flask + Flask-SocketIO backend running SGP4 math on live TLE data from CelesTrak with sub-second calculations. | Proves ability to handle real-time streaming architectures, physics math, and low-latency WebSockets. |
| **4. The 3D Frontend** | Interactive Three.js WebGL globe rendering 2,000+ satellites, orbits, heatmaps, and visibility cones smoothly at 60 FPS. | Demonstrates client-side graphics performance optimization and modern UI engineering skills. |
| **5. Advanced Physics & AI Models** | Monte Carlo Kessler syndrome cascade simulation and line-of-sight elevation masking for 12 global ground stations. | Shows advanced algorithmic modeling capability beyond simple CRUD apps. |
| **6. User Security & Integration** | JWT authentication, SQLite user watchlists/preferences, alert dispatching, and Launch Library 2 API integration. | Proves production readiness, security best practices (RBAC/JWT), and external API integration experience. |

---

## 🎯 Quick Cheat Sheet: Simple Definitions of Tech Terms Used

* **Two-Line Element (TLE)**: A standardized 2-line text data format provided by NORAD/CelesTrak containing the orbital elements of a satellite at a specific epoch time.
* **SGP4 / SDP4 Algorithm**: Simplified General Perturbations models—the mathematical formulas used by aerospace engineers to calculate exact satellite 3D coordinates from TLE data.
* **Conjunction Screening**: The automated process of screening thousands of space objects to detect close approaches within a set safety threshold (e.g., 10 km to 2,000 km).
* **Kessler Syndrome**: A dangerous scenario where space debris collisions create a chain reaction of more debris, rendering orbits unusable.
* **Flask & Flask-SocketIO**: A Python web framework combined with WebSocket protocol handlers for streaming live telemetry bi-directionally without page refreshes.
* **Three.js**: A JavaScript 3D WebGL library used to render GPU-accelerated graphics (like our interactive 3D Earth, satellites, and orbit trajectories) inside a web browser.
* **Ground Station Elevation Masking**: Line-of-sight math that determines whether a satellite is high enough above the horizon to establish radio contact with a ground dish.

---

## ❓ Simple Answers to Quick Follow-Up Questions

### Q1: "Why did you use Flask-SocketIO instead of standard HTTP REST polling for live telemetry?"
> *"HTTP polling creates unnecessary overhead because sending requests every 3 seconds for thousands of satellites wastes bandwidth and CPU resources. Socket.IO maintains a single persistent WebSocket connection, allowing the server to push binary/JSON updates immediately as soon as the SGP4 propagation cycle completes."*

### Q2: "How do you render thousands of satellites on the 3D globe without causing frame drops?"
> *"Instead of creating thousands of heavy individual 3D Mesh objects in Three.js, I used instanced rendering (`InstancedMesh` / `Points`) and GPU-accelerated shaders. This combines all satellite points into a single draw call, allowing the browser GPU to render 2,000+ satellites effortlessly at 60 FPS."*

### Q3: "How does the Kessler Syndrome simulator work?"
> *"When a collision event is triggered, the simulation runs a Monte Carlo model that projects fragment cloud expansion vectors based on object mass and relative impact velocity. It calculates secondary collision probabilities with nearby operational satellites over time to visualize cascading risk."*

### Q4: "What happens if CelesTrak or external data sources are offline?"
> *"I implemented a multi-layer caching system (`cache_layer.py`). TLE data is cached locally with a Time-To-Live (TTL). If CelesTrak times out or goes offline, the backend gracefully serves cached TLE data and notifies the user via an API status flag, keeping the dashboard fully operational."*
