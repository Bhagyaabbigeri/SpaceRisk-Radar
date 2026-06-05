/**
 * Collision Risk Visualizer - UI & Data Module
 * Fetches from Flask backend and plots satellites on the OrbitGlobe.
 */

const API_BASE = 'http://127.0.0.1:5000';
const API_V1_BASE = `${API_BASE}/api/v1`;

// Socket.IO connection (realtime push)
// Provide a resilient initializer so a vendored client that loads
// asynchronously can still be used. `window.socket` will hold the
// active socket when available.
window.socket = window.socket || null;
window._pollIntervals = window._pollIntervals || null;

function initSocketOnce() {
    if (window.socket) return window.socket;
    try {
        if (typeof io !== 'undefined') {
            const s = io(API_BASE);
            s.on('connect', () => {
                console.log('[UI] Socket.IO connected');
                s.emit('set_threshold', { threshold_km: conjunctionThresholdKm });
            });
            s.on('disconnect', () => console.log('[UI] Socket.IO disconnected'));
            s.on('objects', (objects) => {
                if (playbackMode !== 'live') return;
                plotSatellites(objects);
            });
            s.on('threshold_updated', (payload) => {
                if (payload?.threshold_km != null) {
                    conjunctionThresholdKm = payload.threshold_km;
                    updateThresholdUi();
                }
            });
            s.on('conjunctions', (payload) => {
                if (playbackMode !== 'live') return;
                try {
                    const conjs = Array.isArray(payload) ? payload : (payload.conjunctions || []);
                    renderConjunctions(conjs);
                    const count = payload.count ?? conjs.length;
                    setEl('stat-threats', count);
                } catch (e) {
                    console.warn('[UI] conjunctions handler error:', e.message);
                }
            });
            s.on('stats', (payload) => {
                try {
                    updateStatsDisplay(payload);
                } catch (e) {
                    console.warn('[UI] stats handler error:', e.message);
                }
            });
            s.on('ground_visibility', (payload) => {
                if (playbackMode === 'live') renderGroundVisibility(payload);
            });
            s.on('heatmap', (payload) => {
                if (playbackMode === 'live') renderHeatmap(payload);
            });
            s.on('debris_risk', (payload) => {
                if (playbackMode === 'live') renderDebrisRisk(payload);
            });
            s.on('maneuvers', (payload) => {
                if (playbackMode === 'live') renderManeuvers(payload);
            });

            // Stop any polling fallbacks if they exist
            if (window._pollIntervals && Array.isArray(window._pollIntervals)) {
                window._pollIntervals.forEach(id => clearInterval(id));
                window._pollIntervals = null;
            }

            window.socket = s;
            return s;
        } else {
            return null;
        }
    } catch (e) {
        console.warn('[UI] Socket.IO init failed:', e.message);
        return null;
    }
}

let socket = initSocketOnce();

// If the socket factory returned no socket or the socket is not yet connected,
// treat as "unavailable" so the UI can fall back to polling until a real
// connection is established.
if (!socket || (socket && !socket.connected)) {
    console.warn('[UI] Socket.IO client not connected; will retry connection every 2s.');
    const __socketRetry = setInterval(() => {
        const s = initSocketOnce();
        if (s && s.connected) {
            socket = s;
            clearInterval(__socketRetry);
        }
    }, 2000);
}

// ── Global State ──────────────────────────────────────────────────
const globe = new OrbitGlobe();
const satMeshMap = {};   // norad_id → THREE mesh
const conjLines = [];   // conjunction line objects
let allSatData = [];   // full satellite list from API
let visibleSatNames = new Set();
let latestGroundStations = [];
let latestHeatmap = null;
let latestDebrisRisk = null;
let latestLaunches = null;
let latestManeuvers = null;
let activeFilter = 'ALL';
let favoritesFilter = 'ALL';  // 'ALL' or 'FAVORITES'
let currentFavoriteSat = null;  // currently selected satellite for favoriting

// Playback / timeline
const PLAYBACK_WINDOW_MS = 24 * 60 * 60 * 1000;
let playbackMode = 'live';       // 'live' | 'playback'
let playbackPlaying = false;
let playbackTimeMs = Date.now();
let playbackTimer = null;
let playbackFetchBusy = false;

// Conjunction threshold (km)
const THRESHOLD_STORAGE_KEY = 'orbitRiskVisualizer_thresholdKm';
let conjunctionThresholdKm = 500;

// ── Favorites Management ───────────────────────────────────────────
const FAVORITES_STORAGE_KEY = 'orbitRiskVisualizer_favorites';
const AUTH_TOKEN_STORAGE_KEY = 'orbitRiskVisualizer_authToken';
let currentUser = null;

function getFavorites() {
    try {
        const fav = localStorage.getItem(FAVORITES_STORAGE_KEY);
        return fav ? new Set(JSON.parse(fav)) : new Set();
    } catch (e) {
        console.warn('Failed to load favorites:', e);
        return new Set();
    }
}

function saveFavorites(favSet) {
    try {
        localStorage.setItem(FAVORITES_STORAGE_KEY, JSON.stringify(Array.from(favSet)));
    } catch (e) {
        console.warn('Failed to save favorites:', e);
    }
}

function authHeaders() {
    const token = localStorage.getItem(AUTH_TOKEN_STORAGE_KEY);
    return token ? { 'Authorization': `Bearer ${token}` } : {};
}

function setAuthStatus(message) {
    setEl('auth-status', message || '');
}

function setupAuthPanel() {
    document.getElementById('btn-auth-toggle')?.addEventListener('click', () => {
        document.getElementById('auth-panel')?.classList.toggle('open');
    });
    document.getElementById('btn-login')?.addEventListener('click', () => submitAuth('login'));
    document.getElementById('btn-signup')?.addEventListener('click', () => submitAuth('signup'));
    document.getElementById('btn-logout')?.addEventListener('click', logoutUser);
    document.getElementById('btn-save-prefs')?.addEventListener('click', saveRemotePreferences);
}

async function submitAuth(mode) {
    const email = document.getElementById('auth-email')?.value || '';
    const password = document.getElementById('auth-password')?.value || '';
    try {
        const res = await fetch(`${API_V1_BASE}/auth/${mode}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email, password })
        });
        const data = await res.json();
        if (!res.ok) throw new Error(data.error || 'authentication failed');
        localStorage.setItem(AUTH_TOKEN_STORAGE_KEY, data.token);
        currentUser = data.user;
        updateAuthUi();
        await loadRemotePreferences();
        setAuthStatus(mode === 'signup' ? 'Account created.' : 'Logged in.');
    } catch (e) {
        setAuthStatus(e.message);
    }
}

async function restoreAuthSession() {
    const token = localStorage.getItem(AUTH_TOKEN_STORAGE_KEY);
    if (!token) {
        updateAuthUi();
        return;
    }
    try {
        const res = await fetch(`${API_V1_BASE}/auth/me`, { headers: authHeaders() });
        const data = await res.json();
        if (!res.ok) throw new Error(data.error || 'session expired');
        currentUser = data.user;
        updateAuthUi();
        await loadRemotePreferences();
    } catch (e) {
        localStorage.removeItem(AUTH_TOKEN_STORAGE_KEY);
        currentUser = null;
        updateAuthUi();
        setAuthStatus('Session expired.');
    }
}

function logoutUser() {
    localStorage.removeItem(AUTH_TOKEN_STORAGE_KEY);
    currentUser = null;
    updateAuthUi();
    setAuthStatus('Logged out.');
}

function updateAuthUi() {
    const signedIn = Boolean(currentUser);
    const out = document.getElementById('auth-signed-out');
    const inside = document.getElementById('auth-signed-in');
    if (out) out.style.display = signedIn ? 'none' : 'block';
    if (inside) inside.style.display = signedIn ? 'block' : 'none';
    setEl('auth-user-label', currentUser?.email || '-');
    setEl('auth-role-label', currentUser?.role || '-');
}

async function loadRemotePreferences() {
    if (!currentUser) return;
    try {
        const res = await fetch(`${API_V1_BASE}/preferences`, { headers: authHeaders() });
        const data = await res.json();
        if (!res.ok) throw new Error(data.error || 'preferences unavailable');
        const thresholdInput = document.getElementById('pref-alert-threshold');
        const webhookInput = document.getElementById('pref-webhook');
        if (thresholdInput) thresholdInput.value = data.alert_threshold_km ?? 50;
        if (webhookInput) webhookInput.value = data.webhook_url || '';
        if (Array.isArray(data.watched_satellites)) {
            saveFavorites(new Set(data.watched_satellites));
            replotFromCache();
        }
    } catch (e) {
        setAuthStatus(e.message);
    }
}

async function saveRemotePreferences() {
    if (!currentUser) return;
    const threshold = Number(document.getElementById('pref-alert-threshold')?.value || 50);
    const webhookUrl = document.getElementById('pref-webhook')?.value || null;
    try {
        const res = await fetch(`${API_V1_BASE}/preferences`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json', ...authHeaders() },
            body: JSON.stringify({
                alert_threshold_km: threshold,
                webhook_url: webhookUrl,
                preferences: {
                    default_orbit_filter: activeFilter,
                    show_heatmap: true,
                    show_ground_visibility: true
                }
            })
        });
        const data = await res.json();
        if (!res.ok) throw new Error(data.error || 'failed to save preferences');
        setAuthStatus('Preferences saved.');
    } catch (e) {
        setAuthStatus(e.message);
    }
}

async function syncWatchedSatellite(satName, isWatched) {
    if (!currentUser || !satName) return;
    try {
        const url = `${API_V1_BASE}/watched-satellites${isWatched ? '' : '/' + encodeURIComponent(satName)}`;
        await fetch(url, {
            method: isWatched ? 'POST' : 'DELETE',
            headers: { 'Content-Type': 'application/json', ...authHeaders() },
            body: isWatched ? JSON.stringify({ satellite_name: satName }) : undefined
        });
    } catch (e) {
        console.warn('[UI] watched satellite sync failed:', e.message);
    }
}

function toggleFavorite(satName) {
    const favorites = getFavorites();
    if (favorites.has(satName)) {
        favorites.delete(satName);
    } else {
        favorites.add(satName);
    }
    saveFavorites(favorites);
    updateFavoriteButtonState(satName);
    syncWatchedSatellite(satName, favorites.has(satName));
    return favorites.has(satName);
}

function isFavorite(satName) {
    return getFavorites().has(satName);
}

// ── Init ──────────────────────────────────────────────────────────
window.addEventListener('DOMContentLoaded', () => {
    globe.init('globe-container');
    startRenderLoop();
    loadStats();
    loadSatellites();
    loadConjunctions();
    loadAdvancedLayers();
    // If realtime socket is not available, fall back to polling every 30/60 seconds
    if (!socket || (socket && !socket.connected)) {
        window._pollIntervals = window._pollIntervals || [];
        window._pollIntervals.push(setInterval(() => {
            if (playbackMode === 'live') loadSatellites();
        }, 30000));
        window._pollIntervals.push(setInterval(() => {
            if (playbackMode === 'live') loadConjunctions();
        }, 60000));
        window._pollIntervals.push(setInterval(() => {
            if (playbackMode === 'live') loadStats();
        }, 30000));
        window._pollIntervals.push(setInterval(() => {
            if (playbackMode === 'live') loadAdvancedLayers();
        }, 45000));
    }

    loadThresholdFromStorage();
    setupFilters();
    setupSearch();
    setupFavoritesButton();
    setupPlayback();
    setupThreshold();
    setupAuthPanel();
    restoreAuthSession();
    updateThresholdUi();
});

// ── Render Loop ───────────────────────────────────────────────────
function startRenderLoop() {
    function loop() {
        requestAnimationFrame(loop);
        globe.tick();
        animatePulse();
    }
    loop();
}

// ── Load Stats ────────────────────────────────────────────────────
async function loadStats() {
    try {
        const params = buildApiTimeParams();
        params.set('threshold', String(conjunctionThresholdKm));
        const res = await fetch(`${API_BASE}/api/stats?${params}`);
        const data = await res.json();

        // Normalize and update UI elements
        setEl('stat-sats', data.total_satellites ?? data.total_objects ?? 0);
        setEl('stat-threats', data.active_conjunctions ?? 0);
        setEl('stat-avg-alt', data.avg_altitude_km != null ? (data.avg_altitude_km + ' km') : '—');
        setEl('stat-max-speed', data.max_speed_kms != null ? (data.max_speed_kms + ' km/s') : '—');

        // Orbit distribution (fallback-safe)
        const orbitDist = data.orbit_distribution || {};
        setEl('dist-leo', orbitDist['Low Earth Orbit (LEO)'] ?? orbitDist['LEO'] ?? 0);
        setEl('dist-geo', orbitDist['Geostationary Orbit (GEO)'] ?? orbitDist['GEO'] ?? 0);
    } catch (e) {
        console.warn('[UI] Stats fetch failed:', e.message);
    }
}

// ── Load & Plot Satellites ────────────────────────────────────────
async function loadSatellites() {
    if (playbackFetchBusy) return;
    playbackFetchBusy = true;
    try {
        const params = buildApiTimeParams();
        const qs = params.toString();
        const url = qs ? `${API_BASE}/api/objects?${qs}` : `${API_BASE}/api/objects`;
        const res = await fetch(url);
        const objects = await res.json();
        plotSatellites(objects);
    } catch (e) {
        console.warn('[UI] Satellite fetch failed:', e.message);
    } finally {
        playbackFetchBusy = false;
    }
}

function replotFromCache() {
    if (allSatData.length > 0) {
        plotSatellites(allSatData);
    } else {
        loadSatellites();
    }
}


function plotSatellites(objects) {
    try {
        // Normalize incoming objects to a consistent shape used throughout the UI
        const normalized = (objects || []).map(s => {
            const lat = s.lat ?? s.latitude ?? null;
            const lon = s.lon ?? s.longitude ?? s.lng ?? null;
            const alt = s.alt_km ?? s.altitude_km ?? null;
            // Accept multiple possible speed field names for resilience
            const speed = s.speed_kms ?? s.speed_kmh ?? s.speed ?? null;
            const orbit = s.orbit ?? (alt != null ? (alt < 2000 ? 'LEO' : (alt < 35000 ? 'MEO' : (alt < 36500 ? 'GEO' : 'HEO'))) : 'LEO');
            const inclination = s.inclination ?? null;
            const country = s.country ?? 'Unknown';
            return {
                name: s.name,
                lat: lat,
                lon: lon,
                alt_km: alt,
                speed_kms: speed,
                orbit: orbit,
                inclination: inclination,
                country: country,
                norad_id: s.norad_id ?? null,
                object_id: s.object_id ?? null,
                launch_date: s.launch_date ?? null,
                operator: s.operator ?? country,
                decay_date: s.decay_date ?? null,
                tle_epoch: s.tle_epoch ?? null,
                timestamp: s.timestamp ?? null
            };
        });

        allSatData = normalized;

        // Clear old meshes
        Object.values(satMeshMap).forEach(m => globe.removeObject(m));
        Object.keys(satMeshMap).forEach(k => delete satMeshMap[k]);

        let plotted = 0;
        normalized.forEach((sat, idx) => {
            if (!passesFilter(sat)) return;
            if (!hasValidCoords(sat)) return;

            const pos = latLonToVec3(sat.lat, sat.lon, sat.alt_km);
            const color = orbitColor(sat.orbit);
            const mesh = globe.createSatelliteMesh(pos, color);

            if (mesh) {
                mesh.userData = sat;
                
                // Apply special styling for favorited satellites
                if (isFavorite(sat.name)) {
                    // Make favorited satellites brighter and larger
                    mesh.scale.multiplyScalar(1.5);
                    if (mesh.material && mesh.material.emissive) {
                        mesh.material.emissive.setHex(0xffd700); // Gold emissive glow
                        mesh.material.emissiveIntensity = 0.6;
                    }
                }

                if (visibleSatNames.has(sat.name) && mesh.material) {
                    mesh.material.color.setHex(0x10ff9c);
                    mesh.scale.multiplyScalar(1.35);
                }
                
                satMeshMap[idx] = mesh;
                plotted++;
            }
        });

        // Update header badge (fallback id)
        setEl('stat-sats', plotted);

        // Update environment stats (best-effort)
        if (normalized.length > 0) {
            const alts = normalized.map(s => s.alt_km).filter(Boolean);
            const speeds = normalized.map(s => s.speed_kms).filter(Boolean);
            const leoCount = normalized.filter(s => s.orbit === 'LEO').length;
            const geoCount = normalized.filter(s => s.orbit === 'GEO').length;

            setEl('stat-avg-alt', alts.length ? (alts.reduce((a, b) => a + b, 0) / alts.length).toFixed(1) + ' km' : '—');
            setEl('stat-max-speed', speeds.length ? Math.max(...speeds).toFixed(3) + ' km/s' : '—');
            setEl('dist-leo', leoCount);
            setEl('dist-geo', geoCount);
        }

        // Add raycaster click detection
        setupGlobeClick();

        refreshTelemetryIfSelected();
        drawAdvancedOverlays();

        console.log(`[UI] Plotted ${plotted} satellites on globe.`);
    } catch (e) {
        console.warn('[UI] plotSatellites error:', e.message);
    }
}

// ── Load Conjunctions ─────────────────────────────────────────────
async function loadConjunctions() {
    try {
        const params = buildApiTimeParams();
        params.set('threshold', String(conjunctionThresholdKm));
        const res = await fetch(`${API_BASE}/api/conjunctions?${params}`);
        const data = await res.json();
        const conjs = Array.isArray(data) ? data : (data.conjunctions || []);
        if (data.threshold_km != null) {
            conjunctionThresholdKm = data.threshold_km;
            updateThresholdUi();
        }
        renderConjunctions(conjs);
    } catch (e) {
        console.warn('[UI] Conjunction fetch failed:', e.message);
    }
}


function renderConjunctions(conjs) {
    try {
        // Clear old conjunction lines
        conjLines.forEach(l => globe.removeObject(l));
        conjLines.length = 0;

        const list = document.getElementById('conjunctions-list');
        if (list) list.innerHTML = '';

        let threatCount = 0;

        (conjs || []).slice(0, 20).forEach(c => {
            threatCount++;

            // Support both 'obj1/obj2' and 'sat1/sat2' naming
            const name1 = c.obj1 || c.sat1 || c.sat_1;
            const name2 = c.obj2 || c.sat2 || c.sat_2;

            // Draw red line between the two objects if we have their positions
            const obj1 = allSatData.find(s => s.name === name1);
            const obj2 = allSatData.find(s => s.name === name2);
            if (obj1 && obj2) {
                const p1 = latLonToVec3(obj1.lat, obj1.lon, obj1.alt_km);
                const p2 = latLonToVec3(obj2.lat, obj2.lon, obj2.alt_km);
                const line = globe.createConjunctionLine(p1, p2);
                if (line) conjLines.push(line);
            }

            // Add to conjunction warning stream list
            if (list) {
                const div = document.createElement('div');
                div.className = 'conjunction-item';
                div.style.cssText = `
                    padding: 8px 12px;
                    margin: 4px 0;
                    border-left: 3px solid ${c.risk?.color ?? '#ff3b30'};
                    background: rgba(255,59,48,0.08);
                    font-family: 'Rajdhani', sans-serif;
                    font-size: 12px;
                    color: #e0e0e0;
                    border-radius: 2px;
                    cursor: pointer;
                `;
                div.innerHTML = `
                    <span style="color:${c.risk?.color ?? '#ff3b30'}; font-weight:bold;">
                        ${c.risk?.level ?? 'UNKNOWN'}
                    </span>
                    &nbsp;|&nbsp;
                    <strong>${name1 ?? '—'}</strong>
                    &nbsp;↔&nbsp;
                    <strong>${name2 ?? '—'}</strong>
                    &nbsp;&nbsp;
                    <span style="color:#888;">${c.distance_km ?? '?'} km apart</span>
                `;
                div.addEventListener('click', () => fillConjunctionTelemetry(c));
                list.appendChild(div);
            }
        });

        setEl('stat-threats', threatCount);
        console.log(`[UI] ${threatCount} conjunction threats loaded.`);
    } catch (e) {
        console.warn('[UI] renderConjunctions error:', e.message);
    }
}

// Advanced analysis layers: ground-station visibility, maneuvers, launch
// trajectories, Kessler debris clouds, and orbital congestion heatmap.
async function loadAdvancedLayers() {
    await Promise.allSettled([
        loadGroundVisibility(),
        loadHeatmap(),
        loadDebrisRisk(),
        loadLaunches(),
        loadManeuvers()
    ]);
}

async function loadGroundVisibility() {
    try {
        const params = buildApiTimeParams();
        const res = await fetch(`${API_BASE}/api/ground-visibility?${params}`);
        renderGroundVisibility(await res.json());
    } catch (e) {
        console.warn('[UI] ground visibility fetch failed:', e.message);
    }
}

async function loadHeatmap() {
    try {
        const params = buildApiTimeParams();
        const res = await fetch(`${API_BASE}/api/heatmap?${params}`);
        renderHeatmap(await res.json());
    } catch (e) {
        console.warn('[UI] heatmap fetch failed:', e.message);
    }
}

async function loadDebrisRisk() {
    try {
        const params = buildApiTimeParams();
        params.set('threshold', String(conjunctionThresholdKm));
        const res = await fetch(`${API_BASE}/api/debris-risk?${params}`);
        renderDebrisRisk(await res.json());
    } catch (e) {
        console.warn('[UI] debris risk fetch failed:', e.message);
    }
}

async function loadLaunches() {
    try {
        const res = await fetch(`${API_BASE}/api/launches?limit=5`);
        renderLaunches(await res.json());
    } catch (e) {
        console.warn('[UI] launch fetch failed:', e.message);
    }
}

async function loadManeuvers() {
    try {
        const params = buildApiTimeParams();
        const res = await fetch(`${API_BASE}/api/maneuvers?${params}`);
        renderManeuvers(await res.json());
    } catch (e) {
        console.warn('[UI] maneuver fetch failed:', e.message);
    }
}

function renderGroundVisibility(payload) {
    try {
        const visible = payload?.visible || [];
        latestGroundStations = payload?.stations || latestGroundStations;
        visibleSatNames = new Set(visible.map(v => v.satellite).filter(Boolean));
        setEl('ground-visible-count', visible.length);

        const list = document.getElementById('ground-visibility-list');
        if (list) {
            list.innerHTML = '';
            visible.slice(0, 5).forEach(v => {
                const div = document.createElement('div');
                div.className = 'advanced-item';
                div.innerHTML = `<strong>${escapeHtml(v.satellite)}</strong><span>${escapeHtml(v.station_name)} | ${v.elevation_deg} deg | ${formatDuration(v.duration_seconds)}</span>`;
                list.appendChild(div);
            });
            if (!visible.length) {
                list.innerHTML = '<div class="advanced-item"><span>No active station links</span></div>';
            }
        }

        if (allSatData.length) replotFromCache();
        else drawAdvancedOverlays();
    } catch (e) {
        console.warn('[UI] renderGroundVisibility error:', e.message);
    }
}

function renderHeatmap(payload) {
    latestHeatmap = payload;
    setEl('heatmap-max-density', payload?.max_density ?? 0);
    drawAdvancedOverlays();
}

function renderDebrisRisk(payload) {
    latestDebrisRisk = payload;
    setEl('debris-cloud-count', payload?.event_count ?? 0);
    setEl('debris-chain-prob', payload?.chain_probability_sum ?? 0);
    drawAdvancedOverlays();
}

function renderLaunches(payload) {
    latestLaunches = payload;
    const list = document.getElementById('launch-list');
    if (list) {
        list.innerHTML = '';
        (payload?.launches || []).slice(0, 3).forEach(launch => {
            const div = document.createElement('div');
            div.className = 'advanced-item';
            div.style.borderLeftColor = '#ffcc00';
            div.innerHTML = `<strong>${escapeHtml(launch.name)}</strong><span>${escapeHtml(launch.rocket || 'Vehicle TBD')} | ${escapeHtml(launch.orbit || 'Orbit TBD')} | T-${formatDuration(Math.max(0, launch.seconds_until || 0))}</span>`;
            list.appendChild(div);
        });
        if (!(payload?.launches || []).length) {
            list.innerHTML = '<div class="advanced-item"><span>No launch data available</span></div>';
        }
    }
    drawAdvancedOverlays();
}

function renderManeuvers(payload) {
    latestManeuvers = payload;
    const list = document.getElementById('maneuver-list');
    if (list) {
        list.innerHTML = '';
        (payload?.maneuvers || []).slice(0, 3).forEach(m => {
            const div = document.createElement('div');
            div.className = 'advanced-item';
            div.style.borderLeftColor = '#a855f7';
            div.innerHTML = `<strong>${escapeHtml(m.display_name)}</strong><span>${escapeHtml(m.satellite)} | dV ${m.delta_v_mps} m/s | ${m.current_altitude_km} -> ${m.predicted_altitude_km} km</span>`;
            list.appendChild(div);
        });
        if (!(payload?.maneuvers || []).length) {
            list.innerHTML = '<div class="advanced-item"><span>No active maneuver predictions</span></div>';
        }
    }
    drawAdvancedOverlays();
}

function drawAdvancedOverlays() {
    if (!globe?.isInitialized) return;
    globe.clearOverlayObjects();

    (latestHeatmap?.cells || [])
        .filter(cell => heatmapCellPassesFilter(cell))
        .slice(0, 80)
        .forEach(cell => globe.createHeatPoint(cell));

    (latestDebrisRisk?.clouds || []).forEach(cloud => {
        globe.createDebrisCloud(cloud.center, cloud.radius_km, cloud.primary_probability || 0.1);
    });

    (latestLaunches?.launches || []).slice(0, 3).forEach(launch => {
        globe.createPath(launch.trajectory, 0xffcc00, 0.65);
    });

    (latestManeuvers?.maneuvers || []).forEach(m => {
        globe.createPath(m.trajectory_preview, 0xa855f7, 0.8);
    });

    latestGroundStations.forEach(station => {
        globe.createGroundStationMarker(station.latitude, station.longitude, 0xffffff);
    });
}

function heatmapCellPassesFilter(cell) {
    if (activeFilter !== 'ALL' && cell.orbit !== activeFilter) return false;
    const sliderAlt = document.getElementById('slider-alt');
    if (sliderAlt && cell.altitude_band_km?.[0] > Number(sliderAlt.value)) return false;
    return true;
}


function updateStatsDisplay(data) {
    try {
        setEl('stat-sats', data.total_satellites ?? data.total_objects ?? 0);
        setEl('stat-threats', data.active_conjunctions ?? 0);
        setEl('stat-avg-alt', data.avg_altitude_km != null ? (data.avg_altitude_km + ' km') : '—');
        setEl('stat-max-speed', data.max_speed_kms != null ? (data.max_speed_kms + ' km/s') : '—');

        const orbitDist = data.orbit_distribution || {};
        setEl('dist-leo', orbitDist['Low Earth Orbit (LEO)'] ?? orbitDist['LEO'] ?? 0);
        setEl('dist-geo', orbitDist['Geostationary Orbit (GEO)'] ?? orbitDist['GEO'] ?? 0);
    } catch (e) {
        console.warn('[UI] updateStatsDisplay error:', e.message);
    }
}

// ── Filters ───────────────────────────────────────────────────────
function setupFilters() {
    // Orbit type buttons (ALL / LEO / MEO / GEO)
    document.querySelectorAll('[data-orbit]').forEach(btn => {
        btn.addEventListener('click', () => {
            document.querySelectorAll('[data-orbit]').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            activeFilter = btn.dataset.orbit;
            replotFromCache();
        });
    });

    // Favorites toggle buttons
    document.querySelectorAll('[data-fav]').forEach(btn => {
        btn.addEventListener('click', () => {
            document.querySelectorAll('[data-fav]').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            favoritesFilter = btn.dataset.fav || 'ALL';
            replotFromCache();
        });
    });
    // Set default favorites filter button
    const btnFavAll = document.getElementById('btn-favorites-all');
    if (btnFavAll) btnFavAll.classList.add('active');

    // Altitude slider
    const sliderAlt = document.getElementById('slider-alt');
    if (sliderAlt) {
        sliderAlt.addEventListener('input', () => {
            setEl('alt-val', Number(sliderAlt.value).toLocaleString() + ' km');
            replotFromCache();
        });
    }

    // Inclination slider
    const sliderIncl = document.getElementById('slider-incl');
    if (sliderIncl) {
        sliderIncl.addEventListener('input', () => {
            setEl('incl-val', Number(sliderIncl.value).toFixed(1) + '°');
            replotFromCache();
        });
    }

    // Country/Agency dropdown
    const selectCountry = document.getElementById('select-country');
    if (selectCountry) {
        selectCountry.addEventListener('change', () => {
            replotFromCache();
        });
    }

    // Threat classification (kept for compatibility)
    const selectThreat = document.getElementById('select-threat');
    if (selectThreat) {
        selectThreat.addEventListener('change', () => {
            replotFromCache();
        });
    }
}

function passesFilter(sat) {
    // Orbit filter
    if (activeFilter !== 'ALL' && sat.orbit !== activeFilter) return false;

    // Altitude filter
    const sliderAlt = document.getElementById('slider-alt');
    if (sliderAlt && sat.alt_km > Number(sliderAlt.value)) return false;

    // Inclination filter
    const sliderIncl = document.getElementById('slider-incl');
    if (sliderIncl && sat.inclination != null && sat.inclination > Number(sliderIncl.value)) return false;

    // Country/Agency filter
    const selectCountry = document.getElementById('select-country');
    if (selectCountry && selectCountry.value) {
        if (sat.country !== selectCountry.value) return false;
    }

    // Favorites filter
    if (favoritesFilter === 'FAVORITES') {
        if (!isFavorite(sat.name)) return false;
    }

    return true;
}

// ── Search ────────────────────────────────────────────────────────
function setupSearch() {
    const input = document.getElementById('search-name');
    const resultsDiv = document.createElement('div');
    resultsDiv.id = 'search-results';
    resultsDiv.className = 'glass-panel';
    resultsDiv.style.marginTop = '8px';
    // Insert results container after the search input
    input.parentNode.appendChild(resultsDiv);

    let debounceTimer;
    input.addEventListener('input', () => {
        clearTimeout(debounceTimer);
        debounceTimer = setTimeout(() => {
            const query = input.value.trim();
            if (!query) {
                resultsDiv.innerHTML = '';
                return;
            }
            fetch(`${API_BASE}/api/search?query=${encodeURIComponent(query)}`)
                .then(r => r.json())
                .then(data => {
                    // Expected format: { results: [{ name, norad_id, object_id }] }
                    const results = data.results || [];
                    if (results.length) {
                        resultsDiv.innerHTML = results.map(item => `
                            <div class="search-item" data-name="${escapeHtml(item.name)}" data-norad="${item.norad_id || ''}" data-object="${item.object_id || ''}">
                                ${escapeHtml(item.name)} ${item.norad_id ? '(' + item.norad_id + ')' : ''}
                            </div>`).join('');
                        // Attach click handler to each result
                        resultsDiv.querySelectorAll('.search-item').forEach(el => {
                            el.addEventListener('click', () => {
                                const name = el.dataset.name;
                                // set input value and clear results
                                input.value = name;
                                resultsDiv.innerHTML = '';
                                // Trigger a reload to focus on the selected object (if applicable)
                                loadSatellites();
                            });
                        });
                    } else {
                        resultsDiv.innerHTML = '<div class="search-item">No results</div>';
                    }
                })
                .catch(err => {
                    console.error('Search error', err);
                    resultsDiv.innerHTML = '<div class="search-item">Error performing search</div>';
                });
        }, 300);
    });

    if (!input) return;

    input.value = '';
    input.setAttribute('autocomplete', 'off');
    input.setAttribute('autocapitalize', 'off');
    input.setAttribute('spellcheck', 'false');

    let _searchDebounce = null;
    input.addEventListener('input', () => {
        if (_searchDebounce) clearTimeout(_searchDebounce);
        _searchDebounce = setTimeout(async () => {
            const q = input.value.trim();
            if (!q) {
                // Restore normal plotted satellites from cache
                replotFromCache();
                hideTelemetry();
                return;
            }

            try {
                const params = buildApiTimeParams();
                params.set('q', q);
                const res = await fetch(`${API_BASE}/api/search?${params}`);
                if (!res.ok) throw new Error('Search failed');
                const data = await res.json();
                const matches = data.matches || [];

                if (matches.length === 0) {
                    // No matches found: reset mesh scales and hide telemetry
                    Object.values(satMeshMap).forEach(m => { try { m.scale.setScalar(0.4); } catch (e) {} });
                    hideTelemetry();
                    return;
                }

                // Add search matches to allSatData so they can be plotted/processed
                matches.forEach(match => {
                    const exists = allSatData.some(s => s.name === match.name);
                    if (!exists) {
                        allSatData.push({
                            name: match.name,
                            lat: match.latitude,
                            lon: match.longitude,
                            alt_km: match.altitude_km,
                            speed_kms: match.speed_kms,
                            orbit: match.altitude_km < 2000 ? 'LEO' : (match.altitude_km < 35000 ? 'MEO' : (match.altitude_km < 36500 ? 'GEO' : 'HEO')),
                            timestamp: match.timestamp
                        });
                    }
                });

                // Clear existing meshes
                Object.values(satMeshMap).forEach(m => globe.removeObject(m));
                Object.keys(satMeshMap).forEach(k => delete satMeshMap[k]);

                // Plot only the matched satellites (highlighted) and other filtered satellites (shrunk)
                let firstMatch = null;
                const matchNames = new Set(matches.map(m => m.name));

                allSatData.forEach((sat, idx) => {
                    const isSearchResult = matchNames.has(sat.name);
                    const passes = passesFilter(sat);
                    if (!isSearchResult && !passes) return;
                    if (!hasValidCoords(sat)) return;

                    const pos = latLonToVec3(sat.lat, sat.lon, sat.alt_km);
                    const color = orbitColor(sat.orbit);
                    const mesh = globe.createSatelliteMesh(pos, color);

                    if (mesh) {
                        mesh.userData = sat;
                        
                        if (isSearchResult) {
                            // Highlight matched satellites
                            mesh.scale.setScalar(3.5);
                            if (mesh.material && mesh.material.emissive) {
                                mesh.material.emissive.setHex(0x00f0ff); // Cyan glow
                                mesh.material.emissiveIntensity = 0.8;
                            }
                            if (!firstMatch) firstMatch = sat;
                        } else {
                            // Scale down other satellites
                            mesh.scale.setScalar(0.4);
                        }

                        satMeshMap[idx] = mesh;
                    }
                });

                // Set total plotted satellites count in HUD
                setEl('stat-sats', matches.length);

                // Add raycaster click detection
                setupGlobeClick();

                if (firstMatch) {
                    showTelemetry(firstMatch);
                } else {
                    hideTelemetry();
                }
            } catch (e) {
                console.warn('[UI] Backend search failed, falling back to local search:', e.message);
                // Local fallback search (original logic)
                const q_lower = q.toLowerCase();
                let firstMatch = null;
                Object.values(satMeshMap).forEach(mesh => {
                    if (!mesh || !mesh.userData) return;
                    const sat = mesh.userData;
                    const name = (sat.name || '').toString().toLowerCase();
                    const match = name.includes(q_lower);
                    try { mesh.scale.setScalar(match ? 3.5 : 0.4); } catch (e) {}
                    if (match && !firstMatch) firstMatch = sat;
                });
                if (firstMatch) showTelemetry(firstMatch);
            }
        }, 160);
    });
}

// ── Favorites Button ──────────────────────────────────────────────
function setupFavoritesButton() {
    const btn = document.getElementById('btn-favorite-sat');
    if (!btn) return;

    btn.addEventListener('click', () => {
        if (!currentFavoriteSat) return;
        const name = currentFavoriteSat.name;
        toggleFavorite(name);
        updateFavoriteButtonState(name);
        replotFromCache();
    });
}

// ── Playback / Timeline ───────────────────────────────────────────
function setupPlayback() {
    const slider = document.getElementById('playback-slider');
    const btnLive = document.getElementById('btn-live');
    const btnPlay = document.getElementById('btn-playback-play');
    const btnPause = document.getElementById('btn-playback-pause');
    const btnRewind = document.getElementById('btn-playback-rewind');
    const panel = document.getElementById('playback-panel');

    if (!slider) return;

    playbackTimeMs = Date.now();
    slider.max = String(PLAYBACK_WINDOW_MS / 60000);
    slider.value = slider.max;

    slider.addEventListener('input', () => {
        const minsAgo = Number(slider.max) - Number(slider.value);
        playbackTimeMs = Date.now() - minsAgo * 60 * 1000;
        if (playbackMode === 'live') enterPlaybackMode();
        updatePlaybackLabel();
        schedulePlaybackFetch();
    });

    btnLive?.addEventListener('click', () => enterLiveMode());
    btnPlay?.addEventListener('click', () => {
        if (playbackMode === 'live') enterPlaybackMode();
        playbackPlaying = true;
        startPlaybackLoop();
    });
    btnPause?.addEventListener('click', () => {
        playbackPlaying = false;
        stopPlaybackLoop();
    });
    btnRewind?.addEventListener('click', () => {
        if (playbackMode === 'live') enterPlaybackMode();
        playbackTimeMs = Math.max(Date.now() - PLAYBACK_WINDOW_MS, playbackTimeMs - 15 * 60 * 1000);
        syncSliderFromTime();
        updatePlaybackLabel();
        schedulePlaybackFetch();
    });

    panel?.classList.add('playback-live');
}

function enterLiveMode() {
    playbackMode = 'live';
    playbackPlaying = false;
    stopPlaybackLoop();
    playbackTimeMs = Date.now();
    const slider = document.getElementById('playback-slider');
    if (slider) slider.value = slider.max;
    document.getElementById('playback-panel')?.classList.add('playback-live');
    updatePlaybackLabel();
    loadSatellites();
    loadConjunctions();
    loadStats();
    loadAdvancedLayers();
}

function enterPlaybackMode() {
    playbackMode = 'playback';
    document.getElementById('playback-panel')?.classList.remove('playback-live');
    if (playbackTimeMs >= Date.now() - 5000) {
        playbackTimeMs = Date.now() - 60 * 60 * 1000;
    }
    syncSliderFromTime();
    updatePlaybackLabel();
}

function startPlaybackLoop() {
    stopPlaybackLoop();
    playbackTimer = setInterval(() => {
        const speed = Number(document.getElementById('playback-speed')?.value || 300);
        playbackTimeMs += speed * 1000;
        const earliest = Date.now() - PLAYBACK_WINDOW_MS;
        if (playbackTimeMs >= Date.now() - 2000) {
            enterLiveMode();
            return;
        }
        if (playbackTimeMs < earliest) playbackTimeMs = earliest;
        syncSliderFromTime();
        updatePlaybackLabel();
        schedulePlaybackFetch();
    }, 1000);
}

function stopPlaybackLoop() {
    if (playbackTimer) {
        clearInterval(playbackTimer);
        playbackTimer = null;
    }
}

let _playbackFetchTimer = null;
function schedulePlaybackFetch() {
    if (_playbackFetchTimer) clearTimeout(_playbackFetchTimer);
    _playbackFetchTimer = setTimeout(() => {
        loadSatellites();
        loadConjunctions();
        loadStats();
        loadAdvancedLayers();
    }, 350);
}

function syncSliderFromTime() {
    const slider = document.getElementById('playback-slider');
    if (!slider) return;
    const minsAgo = (Date.now() - playbackTimeMs) / 60000;
    slider.value = String(Math.max(0, Number(slider.max) - minsAgo));
}

function updatePlaybackLabel() {
    const el = document.getElementById('playback-time-label');
    if (!el) return;
    if (playbackMode === 'live') {
        el.textContent = 'LIVE — real-time propagation';
        return;
    }
    const d = new Date(playbackTimeMs);
    el.textContent = `REPLAY ${d.toISOString().replace('T', ' ').slice(0, 19)} UTC`
        + (playbackPlaying ? ' ▶' : ' ⏸');
}

function buildApiTimeParams() {
    const params = new URLSearchParams();
    if (playbackMode === 'playback') {
        params.set('at', new Date(playbackTimeMs).toISOString());
    }
    return params;
}

// ── Conjunction threshold ─────────────────────────────────────────
function loadThresholdFromStorage() {
    try {
        const v = localStorage.getItem(THRESHOLD_STORAGE_KEY);
        if (v != null) conjunctionThresholdKm = Math.max(10, Math.min(2000, Number(v)));
    } catch (e) { /* ignore */ }
}

function setupThreshold() {
    const slider = document.getElementById('slider-threshold');
    if (!slider) return;
    slider.value = String(conjunctionThresholdKm);
    let debounce = null;
    slider.addEventListener('input', () => {
        conjunctionThresholdKm = Number(slider.value);
        updateThresholdUi();
        if (debounce) clearTimeout(debounce);
        debounce = setTimeout(applyThreshold, 400);
    });
}

function updateThresholdUi() {
    setEl('threshold-val', `${conjunctionThresholdKm} km`);
    const title = document.getElementById('conjunction-stream-title');
    if (title) {
        title.textContent = `CONJUNCTION WARNING STREAM (THRESHOLD < ${conjunctionThresholdKm} KM)`;
    }
    const slider = document.getElementById('slider-threshold');
    if (slider && Number(slider.value) !== conjunctionThresholdKm) {
        slider.value = String(conjunctionThresholdKm);
    }
}

function applyThreshold() {
    try {
        localStorage.setItem(THRESHOLD_STORAGE_KEY, String(conjunctionThresholdKm));
    } catch (e) { /* ignore */ }
    if (window.socket?.connected) {
        window.socket.emit('set_threshold', { threshold_km: conjunctionThresholdKm });
    }
    loadConjunctions();
    loadStats();
    loadDebrisRisk();
}

// ── Globe Click ───────────────────────────────────────────────────
function setupGlobeClick() {
    const container = document.getElementById('globe-container');
    if (!container || container._clickBound) return;
    container._clickBound = true;

    const raycaster = new THREE.Raycaster();
    const mouse = new THREE.Vector2();

    container.addEventListener('click', (e) => {
        const rect = container.getBoundingClientRect();
        mouse.x = ((e.clientX - rect.left) / rect.width) * 2 - 1;
        mouse.y = -((e.clientY - rect.top) / rect.height) * 2 + 1;

        raycaster.setFromCamera(mouse, globe.camera);
        const hits = raycaster.intersectObjects(Object.values(satMeshMap));
        if (hits.length > 0) {
            showTelemetry(hits[0].object.userData);
        }
    });
}

// ── Telemetry Panel ───────────────────────────────────────────────
function showTelemetry(sat) {
    currentFavoriteSat = sat;
    fillTelemetryFields(sat);
    updateFavoriteButtonState(sat.name);
    fetchSatelliteDetail(sat.name);

    const placeholder = document.getElementById('telemetry-placeholder');
    if (placeholder) placeholder.style.display = 'none';
    const content = document.getElementById('telemetry-content');
    if (content) content.style.display = 'flex';
}

function fillTelemetryFields(sat) {
    setEl('tel-name', sat.name ?? '—');
    setEl('tel-class', sat.orbit ?? '—');
    setEl('tel-country', sat.country ?? 'Unknown');
    setEl('tel-incl', sat.inclination != null ? sat.inclination.toFixed(2) + '°' : '—');
    setEl('tel-alt', sat.alt_km != null ? sat.alt_km.toFixed(1) + ' km' : '—');
    setEl('tel-speed', sat.speed_kms != null ? sat.speed_kms.toFixed(3) + ' km/s' : '—');
    setEl('tel-lat', sat.lat != null ? sat.lat.toFixed(4) + '°' : '—');
    setEl('tel-lon', sat.lon != null ? sat.lon.toFixed(4) + '°' : '—');
    setEl('tel-norad', sat.norad_id != null ? String(sat.norad_id) : '—');
    setEl('tel-object-id', sat.object_id ?? '—');
    setEl('tel-operator', sat.operator ?? sat.country ?? '—');
    setEl('tel-launch', sat.launch_date ?? '—');
    setEl('tel-decay', sat.decay_date ?? '—');
    setEl('tel-tle-epoch', formatEpochLabel(sat.tle_epoch));
}

function fillConjunctionTelemetry(c) {
    // Populate conjunction telemetry fields
    const node = c.obj1 || c.sat1 || c.obj2 || c.sat2 || '-';
    const secondary = c.obj2 || c.sat2 || c.obj1 || c.sat1 || '-';
    setEl('tel-con-node', `${node} ↔ ${secondary}`);
    setEl('tel-con-dist', c.distance_km != null ? `${c.distance_km.toFixed(2)} km` : '-');
    // Probability may be given as fraction (0-1) or percent
    const prob = c.probability != null ? (c.probability * 100).toFixed(3) + '%' : (c.probability_percent || c.probability_pct || '-');
    setEl('tel-con-prob', prob);
    const riskFactors = c.risk_factors || c.risk?.factors || [];
    const factors = Array.isArray(riskFactors) && riskFactors.length ? riskFactors.join(', ') : '-';
    setEl('tel-con-factors', factors);
    setEl('tel-con-maneuver', c.evasion_maneuver || c.evasion_plan || '-');
    // Ensure the card is visible
    const card = document.getElementById('closest-approach-card');
    if (card) card.style.display = 'flex';
    // Ensure telemetry panel is shown (in case no satellite selected)
    const placeholder = document.getElementById('telemetry-placeholder');
    const content = document.getElementById('telemetry-content');
    if (placeholder) placeholder.style.display = 'none';
    if (content) content.style.display = 'flex';
}


function __unusedDuplicateConjunctionTelemetryBlock(c, node) {
    const secondary = c.obj2 || c.sat2 || c.obj1 || c.sat1 || '-';
    setEl('tel-con-node', `${node} ↔ ${secondary}`);
    setEl('tel-con-dist', c.distance_km != null ? `${c.distance_km.toFixed(2)} km` : '-');
    // Probability may be given as fraction (0-1) or percent
    const prob = c.probability != null ? (c.probability * 100).toFixed(3) + '%' : (c.probability_percent != null ? c.probability_percent + '%' : '-');
    setEl('tel-con-prob', prob);
    const factors = c.risk?.factors ? c.risk.factors.join(', ') : '-';
    setEl('tel-con-factors', factors);
    setEl('tel-con-maneuver', c.evasion_plan ?? '-');
    // Ensure the card is visible
    const card = document.getElementById('closest-approach-card');
    if (card) card.style.display = 'flex';
}


async function fetchSatelliteDetail(name) {
    if (!name) return;
    try {
        const params = buildApiTimeParams();
        params.set('name', name);
        const res = await fetch(`${API_BASE}/api/satellite?${params}`);
        if (!res.ok) return;
        const detail = await res.json();
        if (currentFavoriteSat?.name !== name) return;
        fillTelemetryFields({
            ...currentFavoriteSat,
            ...detail,
            lat: detail.latitude ?? currentFavoriteSat.lat,
            lon: detail.longitude ?? currentFavoriteSat.lon,
            alt_km: detail.altitude_km ?? currentFavoriteSat.alt_km
        });
    } catch (e) {
        console.warn('[UI] satellite detail fetch failed:', e.message);
    }
}

function formatEpochLabel(iso) {
    if (!iso) return '—';
    try {
        const d = new Date(iso);
        return d.toISOString().replace('T', ' ').slice(0, 19) + ' UTC';
    } catch (e) {
        return iso;
    }
}

function updateFavoriteButtonState(satName) {
    const btn = document.getElementById('btn-favorite-sat');
    if (!btn) return;
    
    const isFav = isFavorite(satName);
    if (isFav) {
        btn.classList.add('favorited');
        btn.innerHTML = '<ion-icon name="heart"></ion-icon> FAVORITED';
    } else {
        btn.classList.remove('favorited');
        btn.innerHTML = '<ion-icon name="heart-outline"></ion-icon> ADD TO FAVORITES';
    }
}

function hideTelemetry() {
    currentFavoriteSat = null;
    ['tel-name', 'tel-class', 'tel-country', 'tel-incl', 'tel-alt',
        'tel-speed', 'tel-lat', 'tel-lon', 'tel-norad', 'tel-object-id',
        'tel-operator', 'tel-launch', 'tel-decay', 'tel-tle-epoch']
        .forEach(id => setEl(id, '—'));
    const placeholder = document.getElementById('telemetry-placeholder');
    if (placeholder) placeholder.style.display = 'flex';
    const content = document.getElementById('telemetry-content');
    if (content) content.style.display = 'none';
}

// ── Pulse Animation ───────────────────────────────────────────────
let pulseT = 0;
function animatePulse() {
    pulseT += 0.05;
    const scale = 1 + 0.3 * Math.abs(Math.sin(pulseT));
    Object.values(satMeshMap).forEach(mesh => {
        const risk = mesh.userData?.risk_level;
        if (risk === 'CRITICAL' || risk === 'HIGH') {
            mesh.scale.setScalar(scale);
            mesh.material.color.setHex(0xff3b30);
        }
    });
}

// ── Helpers ───────────────────────────────────────────────────────
function hasValidCoords(sat) {
    return sat.lat != null && sat.lon != null
        && !Number.isNaN(Number(sat.lat)) && !Number.isNaN(Number(sat.lon));
}

function refreshTelemetryIfSelected() {
    if (!currentFavoriteSat?.name) return;
    const sat = allSatData.find(s => s.name === currentFavoriteSat.name);
    if (sat) showTelemetry(sat);
    else hideTelemetry();
}

function orbitColor(orbit) {
    switch (orbit) {
        case 'LEO': return 0x00f0ff;   // cyan
        case 'MEO': return 0x8855ff;   // purple
        case 'GEO': return 0xffaa00;   // orange
        default: return 0x00ff88;   // green
    }
}

function formatDuration(seconds) {
    seconds = Math.max(0, Number(seconds) || 0);
    const hours = Math.floor(seconds / 3600);
    const mins = Math.floor((seconds % 3600) / 60);
    if (hours > 0) return `${hours}h ${mins}m`;
    return `${mins}m`;
}

function escapeHtml(value) {
    return String(value ?? '')
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#39;');
}

function setEl(id, value) {
    const el = document.getElementById(id);
    if (el) el.textContent = value;
}
