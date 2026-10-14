# User Guide

This guide walks you through the main tasks you can do in the SpaceRisk Radar dashboard. Each section describes one task, tells you where to look on screen, and explains what the result means.

## Find a satellite

1. Click the **search icon** (🔍) or press the keyboard shortcut shown in the top HUD bar.
2. Type any part of the satellite's name — for example `ISS`, `Hubble`, or `STARLINK`.
3. A dropdown appears with up to 10 matches from the live catalog.
4. Click a result. The globe rotates to centre that satellite, and a detail card shows its current latitude, longitude, altitude, and speed.

!!! tip
    Search is case-insensitive. It also maps visually similar characters, so `0` and `O` match each other.

## Change the screening threshold

The **screening threshold** is the maximum 3D distance (in km) at which two objects are reported as a conjunction. The default is **500 km**.

1. Locate the **Threshold** slider or input field in the left HUD panel.
2. Drag the slider or type a value. The backend accepts values between **10 km and 5000 km** (enforced server-side).
3. Your browser sends a `set_threshold` WebSocket event to the server. The server re-screens all pairs and immediately emits an updated `conjunctions` event.
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
| **Probability** | The derived collision probability as a percentage |
| **Risk factors** | Short labels explaining what drove the score up or down |
| **Evasion maneuver** | A suggested delta-V action (only useful if at least one object is active) |

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

The time slider lets you propagate all orbits at a past or future epoch.

1. Find the **Time** control in the HUD (clock icon or timeline bar).
2. Drag left for the past, right for the future, or type an ISO-8601 date-time directly.
3. The frontend calls `GET /api/objects?at=<ISO-8601>` with the selected timestamp.
4. The globe re-renders all dots at their propagated positions for that moment.

!!! warning
    SGP4 accuracy degrades the further you move from the TLE epoch. For most TLEs this is roughly hours to a few days. Beyond that, positions are illustrative only.

## Check ground station visibility

1. Click the **Ground Stations** layer toggle in the HUD.
2. Five ground stations appear on the globe as labelled markers: White Sands, Goldstone DSN, Madrid DSN, Canberra DSN, and Sriharikota.
3. A visibility cone radiates from each station. Satellites inside a cone are above the station's minimum elevation angle (10° for most stations).
4. A visibility list in the panel shows which satellites are currently visible from which station, the elevation angle, and an estimated pass duration.

## Favorites and account panel

### Saving a favorite

1. Open the satellite detail card (search for a satellite, then click it).
2. Click the **star icon** (⭐) in the card header.
3. The satellite name is saved to your watchlist. If you are signed in, the watchlist is stored in the server-side user profile via `POST /api/v1/watched-satellites`. If you are not signed in, it is stored in browser local storage.

### Account panel

1. Click the **account icon** (👤) in the top-right of the HUD.
2. If you are not signed in, you see options to **Sign Up** or **Log In**.
   - Sign up: sends `POST /api/v1/auth/signup` with your email, password, and display name.
   - Log in: sends `POST /api/v1/auth/login` and receives a JWT token valid for 8 hours.
3. Once signed in, the panel shows your display name and a link to preferences.
4. Preferences (theme, alert settings) are stored via `PUT /api/v1/preferences`.

![SpaceRisk Radar account and control panel](assets/SpaceRisk-Rader5.png)
*The account and control panel showing sign-in options and watchlist management.*
