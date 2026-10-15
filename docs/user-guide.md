# User Guide

This guide walks you through the main tasks you can do in the SpaceRisk Radar dashboard. Each section describes one task, tells you where to look on screen, and explains what the result means.

## Find a satellite

1. In the left HUD panel, click the **Search Object** field (placeholder: `Enter Satellite Name (e.g. ISS, STARLINK)...`).
2. Type any part of the satellite's name — for example `ISS`, `Hubble`, or `STARLINK`.
3. A dropdown appears with up to 10 matches from the live catalog.
4. Click a result. The globe rotates to centre that satellite, and a detail card shows its current latitude, longitude, altitude, and speed.

!!! tip
    Search is case-insensitive and matches a substring of the name. The backend also maps visually similar characters, such as `0` and `O`.

## Change the screening threshold

The **screening threshold** is the maximum 3D distance (in km) at which two objects are reported as a conjunction. The default is **500 km**.

1. Locate the **Conjunction Threshold** slider in the left HUD panel.
2. Drag the slider to choose a value from **10 km to 2000 km**. The server also accepts threshold values from **10 km to 5000 km** and clamps received values to that range.
3. Your browser sends a `set_threshold` WebSocket event to the server. The server re-screens the propagated objects and emits an updated `conjunctions` event on its next cycle.
4. The conjunction count badge and the list below it refresh within one 3-second cycle.

!!! note
    Lowering the threshold reduces the number of conjunctions shown. Raising it above a few hundred km typically reveals many low-risk pairs because objects are screened by their instantaneous 3D distance, not a predictive close-approach calculation.

## Read a conjunction and its risk level

Each row in the conjunction list shows:

| Field | What it means |
|---|---|
| **Object 1 / Object 2** | Names of the two objects |
| **Distance** | Current 3D distance between them in km |
| **Risk level** | CRITICAL / HIGH / MEDIUM / LOW — see below |
| **Probability** | The heuristic probability score, displayed as a percentage |
| **Risk factors** | Short labels explaining what drove the score up or down |
| **Evasion maneuver** | A rule-based illustrative suggestion; it is not an operational maneuver recommendation |

### Risk levels

Risk levels come from the probability value, not directly from distance:

| Level | Probability threshold | Colour |
|---|---|---|
| CRITICAL | ≥ 0.1 % | Red |
| HIGH | ≥ 0.01 % | Orange |
| MEDIUM | ≥ 0.0001 % | Yellow |
| LOW | below 0.0001 % | Cyan |

See [Limitations](limitations.md#probability-model) for an important note on what this probability estimate is and is not.

## Replay a time with the slider

The **ORBIT TIMELINE — 24H REPLAY** slider propagates tracked objects at times from the past 24 hours up to the live feed.

1. Find **ORBIT TIMELINE — 24H REPLAY** at the bottom of the dashboard.
2. Drag its slider left to select an earlier time. Use **LIVE**, **⏪ 15m**, **▶**, or **⏸** to return to live data, rewind, play, or pause.
3. In replay mode, the frontend calls `GET /api/objects?at=<ISO-8601>` with the selected timestamp. The API accepts other valid timestamps, but the dashboard control covers only the past 24 hours.
4. The globe re-renders all dots at their propagated positions for that moment.

!!! warning
    Position accuracy generally degrades as the TLE epoch gets older, but the app does not estimate position error from epoch age. Check the displayed TLE Epoch; stale-element positions are illustrative.

## Check ground station visibility

1. Find the **GROUND VISIBILITY** section in the left HUD panel.
2. The app checks visibility from five stations: White Sands, Goldstone DSN, Madrid DSN, Canberra DSN, and Sriharikota.
3. A satellite is reported visible when its elevation reaches the station's **10° minimum elevation angle**.
4. The panel lists visible satellites, elevation, and an approximate pass-duration estimate based on elevation and altitude.

## Favorites and account panel

### Saving a favorite

1. Open the satellite detail card (search for a satellite, then click it).
2. Click the **star icon** (⭐) in the card header.
3. The favorite is saved in browser local storage. When signed in, the app also syncs it to the server-side watchlist via `POST /api/v1/watched-satellites`; signing in loads the account's watched satellites into the favorites list.

### Account panel

1. Click the **account icon** (👤) in the top-right of the HUD.
2. If you are not signed in, the panel has **LOGIN** and **SIGNUP** buttons.
   - Sign up: sends `POST /api/v1/auth/signup` with your email and password. The API accepts an optional display name; the dashboard does not show a display-name field.
   - Log in: sends `POST /api/v1/auth/login` and receives a JWT token valid for 8 hours.
3. Once signed in, the panel shows your email and role, plus **Alert Threshold KM**, **Webhook URL**, **SAVE PREFS**, and **LOGOUT** controls.
4. **SAVE PREFS** sends alert-threshold, webhook URL, and preference values via `PUT /api/v1/preferences`.

![SpaceRisk Radar account and control panel](assets/SpaceRisk-Rader5.png)
*The account and control panel showing sign-in options and watchlist management.*
