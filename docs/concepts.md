# Concepts

This page defines the key terms used throughout SpaceRisk Radar. Each definition uses plain English first, then a short analogy, then a reference.

---

## Two-Line Element Set (TLE)

A **Two-Line Element Set** (TLE) is a compact, standardized text format that encodes a satellite's orbital state at a specific moment in time called the *epoch*. A TLE consists of exactly three lines: a name line and two data lines.

Each data line encodes values such as the orbital inclination, the rate at which the orbit drifts, and where the satellite was in its orbit at the epoch. These numbers are all you need to calculate where the satellite will be at any later (or earlier) time, as long as you also have an accurate propagation model.

**Analogy:** Think of a TLE as a flight plan timestamp. If you know a plane's position, heading, altitude, and airspeed at noon, you can extrapolate where it will be at 12:10 — as long as it does not change course. A TLE gives you the orbital equivalent of those four values.

**Reference:** Kelso, T.S. *CelesTrak: Two-Line Element Set Format*. [https://celestrak.org/columns/v04n03/](https://celestrak.org/columns/v04n03/)

---

## SGP4 (Simplified General Perturbations 4)

**SGP4** is the mathematical model used to compute a satellite's position from a TLE. It takes the orbital elements in the TLE plus a target date and time, and returns a 3D position and velocity vector. Those vectors are then converted to latitude, longitude, and altitude for display on the globe.

SGP4 accounts for:

- The Earth's slightly flattened shape (the J2 zonal harmonic is the dominant term).
- Atmospheric drag for objects in low Earth orbit.
- Smaller gravitational perturbations from the Moon and the Sun for deep-space objects (the SDP4 variant).

SpaceRisk Radar uses the [`python-sgp4`](https://pypi.org/project/sgp4/) library, which is a Python wrapper around the canonical C implementation.

**Analogy:** SGP4 is like a physics engine in a video game — a simplified model of reality that is accurate enough for planning but not for precision navigation. A real spacecraft uses onboard sensors and GPS for millimetre-level accuracy; SGP4 works from a two-day-old snapshot.

**Reference:** Vallado, D.A., Crawford, P., Hujsak, R., Kelso, T.S. (2006). *Revisiting Spacetrack Report #3*. AIAA 2006-6753.

---

## Conjunction

A **conjunction** occurs when two space objects come within a defined distance of each other. SpaceRisk Radar detects conjunctions by computing the 3D distance between every pair of tracked objects and flagging any pair closer than the *screening threshold* (default: 500 km).

The 3D distance is computed using the Haversine formula for the great-circle surface distance, then extended with the Pythagorean theorem to include the altitude difference. This gives the straight-line distance through space between the two objects at the moment they are propagated.

A conjunction is **not** the same as a collision. Most conjunctions involve two objects that are far enough apart that the collision probability is very low. The word "conjunction" in space operations simply means "a close pass worth looking at."

**Analogy:** Imagine two cars on a motorway whose GPS dots appear close on a map. They might be on different lanes, travelling in the same direction at similar speed, or crossing at an interchange — the map view alone does not tell you the risk. A conjunction is the same: two dots that look close at one snapshot in time.

**Reference:** NASA Conjunction Assessment Risk Analysis (CARA). [https://www.nasa.gov/conjunction-assessment-risk-analysis/](https://www.nasa.gov/conjunction-assessment-risk-analysis/)

---

## Collision Probability

In SpaceRisk Radar, **collision probability** is a dimensionless score derived from a log-linear formula, not from a rigorous statistical model.

Here is how it works, directly from `backend/risk_engine.py`:

1. **Base score** — Start with `base_score = -2.0 - 0.08 × distance_km`. At zero separation, `base_score = -2.0` (probability = 1 %). Each kilometre of separation subtracts 0.08 from the exponent, so the probability falls off exponentially with distance.

2. **Orbit adjustment** — If either object is in LEO, add +0.3 (LEO is more congested). If both are in GEO, subtract −0.4 (GEO objects tend to be station-kept and spaced).

3. **Velocity adjustment** — `speed_adj = 0.05 × (average_speed − 7.0)`. Faster objects get a slightly higher score.

4. **Debris adjustment** — If either object is classified as debris (detected by name or operator string matching), add +0.6 (debris cannot manoeuvre). If both are active payloads, subtract −0.3 (they can coordinate an avoidance manoeuvre).

5. **Inclination adjustment** — If both objects are in polar orbits (inclination 70°–110°), add +0.4 (polar orbits intersect at high relative angles and speeds).

6. **Clamp and convert** — The sum is clamped to the range `[−8, −1]`, then converted: `probability = 10^final_score`. This gives values between 10⁻⁸ and 10⁻¹.

!!! warning "This is not a rigorous Pc calculation"
    Operational space agencies use probability of collision (Pc) methods that require a full position-covariance matrix for both objects. SpaceRisk Radar does **not** use covariance. The score here is a heuristic intended to rank conjunctions by relative severity, not to produce operationally certified probabilities.

**Reference:** Alfano, S. (2005). *A numerical implementation of spherical object collision probability*. Journal of Astronautical Sciences, 53(1), 103–109.

---

## Kessler Syndrome

**Kessler syndrome** (also called the Kessler effect or collisional cascading) is a scenario where the density of objects in low Earth orbit becomes high enough that collisions generate debris, which causes more collisions, which generate more debris — a self-sustaining chain reaction that could eventually make certain orbital shells unusable.

SpaceRisk Radar simulates this risk by taking the closest conjunctions in the current snapshot and estimating how many secondary objects a hypothetical collision at each conjunction point would threaten. The simulation is deterministic (no random sampling). See [Limitations — Kessler module](limitations.md#kessler-module) for what the model does and does not capture.

**Analogy:** Imagine a busy junction where one crash blocks the road, causing a pile-up, which forces traffic onto side streets that then also jam. Kessler syndrome is the orbital version: one collision creates a debris cloud that forces other satellites to dodge, and some of those manoeuvres may fail, leading to more impacts.

**Reference:** Kessler, D.J., Cour-Palais, B.G. (1978). *Collision frequency of artificial satellites: The creation of a debris belt*. Journal of Geophysical Research, 83(A6), 2637–2646.
