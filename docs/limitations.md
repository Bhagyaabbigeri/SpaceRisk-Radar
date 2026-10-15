# Limitations

Read this page before citing any numbers from SpaceRisk Radar in a report or presentation.

---

## TLE accuracy and epoch age

A TLE is a snapshot of an orbit at a specific moment (the epoch). Satellite positions degrade in accuracy as you move away from the epoch, due to:

- **Atmospheric drag** (especially in LEO below ~500 km, where the residual atmosphere changes with solar activity).
- **Solar radiation pressure** on large, light satellites.
- **Third-body gravitational effects** from the Moon and Sun (mainly for GEO and HEO).
- **Orbital manoeuvres** — if the satellite thrusts after the TLE epoch, the TLE is immediately outdated.

Position error increases as the TLE epoch gets older, but SpaceRisk Radar does not calculate or report an error bound based on TLE age. Treat propagated positions as illustrative when the epoch is stale; inspect `tle_epoch` in the API response.

The background worker checks the TLE catalog every 10 minutes. A network fetch is normally attempted when the healthy cache is older than 2 hours; a missing or unhealthy cache also triggers an attempt. Each object's `tle_epoch` field in the API response indicates the element-set epoch.

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
- It does not use a covariance matrix for either object. Operational Pc calculations use position-uncertainty data that this application does not calculate or load.
- The adjustments for orbit type, velocity, debris status, and inclination are engineering judgment values, not fits to historical collision data.

### Worked examples

For these examples, both objects are non-debris LEO objects with `speed_kms = 7.5`, `inclination = 51.6`, and non-debris operator/country values. The LEO, speed, and coordinated-payload adjustments are therefore +0.3, +0.025, and −0.3; the score is clamped to the range −8 to −1 before exponentiation.

| Distance (km) | Probability | Level |
|---:|---:|---|
| 5 | 0.004216965 | CRITICAL |
| 10 | 0.001678804 | CRITICAL |
| 50 | 0.000001059254 | MEDIUM |
| 100 | 0.00000001 | LOW |
| 142 | 0.00000001 | LOW |
| 500 | 0.00000001 | LOW |

**Use these numbers to rank conjunctions by relative severity, not to make operational manoeuvre decisions.**

The risk level labels map to probability thresholds as follows:

| Level | Condition |
|---|---|
| CRITICAL | probability ≥ 0.001 (0.1 %) |
| HIGH | probability ≥ 0.0001 (0.01 %) |
| MEDIUM | probability ≥ 0.000001 (0.0001 %) |
| LOW | probability < 0.000001 |

These are application-specific thresholds, not operational decision thresholds.

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

SpaceRisk Radar parses the catalog feed without filtering TLEs by object type before selecting the first 2,000 entries to propagate. Since catalog feeds can contain real debris and rocket bodies, these can appear in that prefix if present in the feed and ordering. Separately, when at least one catalog object propagates, the app appends a **synthetic test object** called `TEST_DEBRIS_X` near the first successfully propagated object. This object is not real debris; it is used to exercise the risk display.

You can identify it in the API by the field `"operator": "Simulated"`.

---

## No hosted demo

There is no hosted demo of SpaceRisk Radar. To try the app, follow the [Getting Started](getting-started.md) guide to run it on your own machine.
