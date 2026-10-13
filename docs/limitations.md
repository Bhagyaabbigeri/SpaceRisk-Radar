# Limitations

Read this page before citing any numbers from SpaceRisk Radar in a report or presentation.

---

## TLE accuracy and epoch age

A TLE is a snapshot of an orbit at a specific moment (the epoch). Satellite positions degrade in accuracy as you move away from the epoch, due to:

- **Atmospheric drag** (especially in LEO below ~500 km, where the residual atmosphere changes with solar activity).
- **Solar radiation pressure** on large, light satellites.
- **Third-body gravitational effects** from the Moon and Sun (mainly for GEO and HEO).
- **Orbital manoeuvres** — if the satellite thrusts after the TLE epoch, the TLE is immediately outdated.

As a rough guide, a TLE published today for an average LEO object is accurate to within a few kilometres for the first day, tens of kilometres after 2–3 days, and should be treated as illustrative beyond a week.

SpaceRisk Radar caches TLEs for 2 hours before re-fetching. Each object's `tle_epoch` field in the API response tells you exactly how old the element set is.

---

## SGP4 accuracy limits

SGP4 is the standard propagation model for publicly available TLEs, but it is a *simplified* model:

- It does not use continuous measurement updates (unlike operational systems that track objects with radar).
- The J2 through J4 zonal harmonics it models are approximations; higher-order terms are ignored.
- Atmospheric density estimates use a static model; actual density varies with the 11-year solar cycle and geomagnetic storms.
- For deep-space objects (period > 225 minutes), the SDP4 variant is used, which introduces additional approximations.

If you need sub-kilometre accuracy, you need operational data from CSpOC (Combined Space Operations Centre) or a high-fidelity propagator like HPOP.

---

## Probability model

The collision probability shown in SpaceRisk Radar is a **heuristic score**, not a rigorous Pc (probability of collision) calculation.

Specifically:

- It is derived from the formula `probability = 10^(base_score + adjustments)` where `base_score = -2.0 - 0.08 × distance_km`.
- It does not use a covariance matrix for either object. Operational Pc calculations require covariance data (uncertainty ellipsoids in position and velocity) which is not publicly available for most objects.
- The adjustments for orbit type, velocity, debris status, and inclination are engineering judgment values, not fits to historical collision data.

**Use these numbers to rank conjunctions by relative severity, not to make operational manoeuvre decisions.**

The risk level labels map to probability thresholds as follows:

| Level | Condition |
|---|---|
| CRITICAL | probability ≥ 0.001 (0.1 %) |
| HIGH | probability ≥ 0.0001 (0.01 %) |
| MEDIUM | probability ≥ 0.000001 (0.0001 %) |
| LOW | probability < 0.000001 |

These thresholds are illustrative. Operational agencies such as NASA use their own tiered thresholds based on Pc values derived from covariance-propagated screening volumes.

---

## Object propagation cap

The live view propagates at most **2000 objects** per 3-second cycle (`PROPAGATION_LIMIT = 2000` in `app.py`). CelesTrak's full catalog contains many more entries. Objects beyond position 2000 are not shown on the globe and are not included in conjunction screening during that cycle.

This cap exists to keep CPU usage and WebSocket payload size manageable on a single-process server. The threshold of 2000 was chosen as a balance between visual density and performance; it is not a scientifically meaningful cutoff.

---

## Kessler module

The Kessler cascade simulator (`kessler.py`) is illustrative:

- It takes the top 5 closest conjunctions and simulates hypothetical debris clouds.
- **Fragment count** is estimated from a simple formula tied to miss distance (`debris_count = 80 + max(0, 500 - miss_distance) × 1.8`), not from validated fragmentation models such as NASA's MASTER or the Squire model.
- **Primary probability** uses `min(0.85, 0.015 × (50 / miss_distance)^1.35)` — a hand-tuned curve, not a physics-derived relationship.
- The model is **deterministic**; it contains no random sampling (no Monte Carlo).
- It does not simulate debris propagation over time or the build-up of debris belts.

The output is useful for understanding *which* conjunctions could have the largest cascading impact if a collision occurred, but the absolute probability numbers should not be taken as predictions.

---

## Simulated vs. real debris

SpaceRisk Radar fetches TLEs from CelesTrak's catalog, which includes both active satellites and cataloged debris objects. However, to guarantee at least one conjunction in the live view, the app always injects a **synthetic test object** called `TEST_DEBRIS_X` near the first object in the catalog. This object is not a real satellite or debris fragment — it is a placeholder for testing the risk display.

You can identify it in the API by the field `"operator": "Simulated"`.
