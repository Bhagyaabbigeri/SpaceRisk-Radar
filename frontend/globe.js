/**
 * Collision Risk Visualizer - 3D Globe Module
 * Procedural Earth sphere — no external texture files required.
 */

const EARTH_RADIUS_UNITS = 2.0;
const EARTH_RADIUS_KM = 6378.137;

/**
 * Converts geodetic lat/lon/alt to a THREE.Vector3 in scene space.
 */
function latLonToVec3(lat, lon, alt) {
    const phi   = (90 - lat) * (Math.PI / 180);
    const theta = (lon + 90) * (Math.PI / 180);
    const r     = EARTH_RADIUS_UNITS + (alt * EARTH_RADIUS_UNITS) / EARTH_RADIUS_KM;

    return new THREE.Vector3(
        r * Math.sin(phi) * Math.sin(theta),
        r * Math.cos(phi),
        r * Math.sin(phi) * Math.cos(theta)
    );
}

class OrbitGlobe {
    constructor() {
        this.scene          = null;
        this.camera         = null;
        this.renderer       = null;
        this.controls       = null;
        this.earthMesh      = null;
        this.atmosphereGrid = null;
        this.starsPoints    = null;
        this.overlayObjects = [];
        this.isInitialized  = false;
    }

    init(containerId) {
        const container = document.getElementById(containerId);
        if (!container) {
            console.error(`Globe container #${containerId} not found.`);
            return;
        }

        // Keep a reference to the container and ensure it has sensible sizing
        this.container = container;
        if (!container.style.position) container.style.position = 'relative';
        container.style.overflow = 'hidden';

        // Get size from the container (fall back to window if not available)
        const width  = container.clientWidth || window.innerWidth;
        const height = container.clientHeight || window.innerHeight;

        try {
            /* ── Scene & Camera ───────────────────────────────────── */
            this.scene  = new THREE.Scene();
            this.camera = new THREE.PerspectiveCamera(45, width / height, 0.1, 1000);
            this.camera.position.set(0, 0, 7.5);

            /* ── Renderer ─────────────────────────────────────────── */
            this.renderer = new THREE.WebGLRenderer({ antialias: true, alpha: false });
            this.renderer.setSize(width, height);
            this.renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
            this.renderer.setClearColor(0x030712, 1);   // match body bg
            container.appendChild(this.renderer.domElement);

            /* ── Orbit Controls ───────────────────────────────────── */
            this.controls = new THREE.OrbitControls(this.camera, this.renderer.domElement);
            this.controls.enableDamping  = true;
            this.controls.dampingFactor  = 0.05;
            this.controls.minDistance    = 3.0;
            this.controls.maxDistance    = 25.0;

            /* ── Lighting ─────────────────────────────────────────── */
            this.scene.add(new THREE.AmbientLight(0xffffff, 0.7));
            const sun = new THREE.DirectionalLight(0x88ccff, 1.2);
            sun.position.set(5, 3, 5);
            this.scene.add(sun);

            /* ── Earth (procedural, no texture file needed) ───────── */
            const earthGeo = new THREE.SphereGeometry(EARTH_RADIUS_UNITS, 64, 64);
            const earthMat = new THREE.MeshPhongMaterial({
                color:     0x1a4a8a,   // vivid ocean blue
                emissive:  0x051530,
                shininess: 25,
            });
            this.earthMesh = new THREE.Mesh(earthGeo, earthMat);
            this.scene.add(this.earthMesh);

            // Attempt to load a real NASA Blue Marble texture from a reliable CDN.
            // If it fails the blue Phong sphere is already perfectly visible.
            const loader = new THREE.TextureLoader();
            loader.load(
                'https://cdn.jsdelivr.net/gh/mrdoob/three.js@r128/examples/textures/planets/earth_atmos_2048.jpg',
                (tex) => {
                    this.earthMesh.material.map          = tex;
                    this.earthMesh.material.emissive.set(0x000000);
                    this.earthMesh.material.color.set(0xffffff);
                    this.earthMesh.material.needsUpdate  = true;
                    console.log('[Globe] NASA Blue Marble texture applied.');
                },
                undefined,
                () => console.warn('[Globe] Texture CDN unreachable — using procedural blue sphere.')
            );

            /* ── Cyan Wireframe Grid (atmosphere overlay) ─────────── */
            const gridGeo = new THREE.SphereGeometry(EARTH_RADIUS_UNITS + 0.015, 36, 36);
            const gridMat = new THREE.MeshBasicMaterial({
                color:       0x00f0ff,
                wireframe:   true,
                transparent: true,
                opacity:     0.12,
            });
            this.atmosphereGrid = new THREE.Mesh(gridGeo, gridMat);
            this.scene.add(this.atmosphereGrid);

            /* ── Atmosphere Glow (additive shell) ─────────────────── */
            const glowGeo = new THREE.SphereGeometry(EARTH_RADIUS_UNITS + 0.08, 32, 32);
            const glowMat = new THREE.MeshBasicMaterial({
                color:       0x0055ff,
                transparent: true,
                opacity:     0.06,
                side:        THREE.BackSide,
            });
            this.scene.add(new THREE.Mesh(glowGeo, glowMat));

            /* ── Starfield ────────────────────────────────────────── */
            const starPositions = new Float32Array(4500);
            for (let i = 0; i < 4500; i++) starPositions[i] = (Math.random() - 0.5) * 120;
            const starGeo = new THREE.BufferGeometry();
            starGeo.setAttribute('position', new THREE.BufferAttribute(starPositions, 3));
            this.starsPoints = new THREE.Points(starGeo, new THREE.PointsMaterial({
                color: 0xffffff, size: 0.05, transparent: true, opacity: 0.75,
            }));
            this.scene.add(this.starsPoints);

            /* ── Resize handler ───────────────────────────────────── */
            window.addEventListener('resize', () => this._onResize());

            this.isInitialized = true;
            console.log('[Globe] Three.js scene initialised successfully.');

        } catch (err) {
            console.error('[Globe] WebGL initialisation failed:', err);
            container.innerHTML = `
                <div style="display:flex;flex-direction:column;align-items:center;
                            justify-content:center;height:100%;color:#00f0ff;
                            font-family:'Orbitron',sans-serif;text-align:center;padding:20px;">
                    <div style="font-size:48px;margin-bottom:16px;">🌐</div>
                    <div style="font-size:14px;font-weight:bold;">ORBITAL 3D ENGINE OFFLINE</div>
                    <div style="font-size:11px;opacity:0.6;margin-top:8px;max-width:380px;
                                font-family:'Rajdhani',sans-serif;line-height:1.5;">
                        WebGL is unavailable. Telemetry stream, filters, and conjunction
                        alerts are still fully operational below.
                    </div>
                </div>`;
            this.isInitialized = false;
        }
    }

    _onResize() {
        if (!this.isInitialized) return;
        const width = (this.container && this.container.clientWidth) || window.innerWidth;
        const height = (this.container && this.container.clientHeight) || window.innerHeight;
        this.camera.aspect = width / height;
        this.camera.updateProjectionMatrix();
        this.renderer.setSize(width, height);
    }

    tick() {
        if (!this.isInitialized) return;
        if (this.earthMesh)      this.earthMesh.rotation.y      += 0.0005;
        if (this.atmosphereGrid) this.atmosphereGrid.rotation.y -= 0.0002;
        if (this.starsPoints)    this.starsPoints.rotation.y    += 0.00005;
        this.controls.update();
        this.renderer.render(this.scene, this.camera);
    }

    /** Place a coloured dot at a geodetic position. */
    createSatelliteMesh(position, colorHex = 0x00f0ff) {
        if (!this.isInitialized) return null;
        const mesh = new THREE.Mesh(
            new THREE.SphereGeometry(0.022, 8, 8),
            new THREE.MeshBasicMaterial({ color: colorHex })
        );
        mesh.position.copy(position);
        this.scene.add(mesh);
        return mesh;
    }

    /** Remove and dispose a mesh from the scene. */
    removeObject(obj) {
        if (!this.isInitialized || !obj) return;
        this.scene.remove(obj);
        if (obj.geometry) obj.geometry.dispose();
        if (obj.material) {
            Array.isArray(obj.material)
                ? obj.material.forEach(m => m.dispose())
                : obj.material.dispose();
        }
    }

    /** Draw a dashed orbital ring approximation. */
    createOrbitLine(lat, lon, alt) {
        if (!this.isInitialized) return null;
        const r    = EARTH_RADIUS_UNITS + (alt * EARTH_RADIUS_UNITS) / EARTH_RADIUS_KM;
        const inc  = Math.max(Math.abs(lat), 35) * (Math.PI / 180);
        const raan = lon * (Math.PI / 180);
        const pts  = [];

        for (let i = 0; i <= 120; i++) {
            const u    = (i / 120) * 2 * Math.PI;
            const xOrb = r * Math.cos(u);
            const yOrb = r * Math.sin(u) * Math.sin(inc);
            const zOrb = r * Math.sin(u) * Math.cos(inc);
            pts.push(new THREE.Vector3(
                xOrb * Math.cos(raan) - zOrb * Math.sin(raan),
                yOrb,
                xOrb * Math.sin(raan) + zOrb * Math.cos(raan)
            ));
        }

        const geo  = new THREE.BufferGeometry().setFromPoints(pts);
        const mat  = new THREE.LineDashedMaterial({
            color: 0x00f0ff, dashSize: 0.1, gapSize: 0.05,
            transparent: true, opacity: 0.4,
        });
        const line = new THREE.Line(geo, mat);
        line.computeLineDistances();
        this.scene.add(line);
        return line;
    }

    /** Draw a red danger connector between two 3-D points. */
    createConjunctionLine(p1, p2) {
        if (!this.isInitialized) return null;
        const geo  = new THREE.BufferGeometry().setFromPoints([p1, p2]);
        const mat  = new THREE.LineBasicMaterial({
            color: 0xff3b30, linewidth: 2, transparent: true, opacity: 0.85,
        });
        const line = new THREE.Line(geo, mat);
        this.scene.add(line);
        return line;
    }

    clearOverlayObjects() {
        this.overlayObjects.forEach(obj => this.removeObject(obj));
        this.overlayObjects = [];
    }

    trackOverlayObject(obj) {
        if (obj) this.overlayObjects.push(obj);
        return obj;
    }

    createGroundStationMarker(lat, lon, labelColor = 0xffffff) {
        if (!this.isInitialized) return null;
        const pos = latLonToVec3(lat, lon, 0);
        const mesh = new THREE.Mesh(
            new THREE.ConeGeometry(0.035, 0.1, 10),
            new THREE.MeshBasicMaterial({ color: labelColor })
        );
        mesh.position.copy(pos);
        mesh.lookAt(new THREE.Vector3(0, 0, 0));
        this.scene.add(mesh);
        return this.trackOverlayObject(mesh);
    }

    createPath(points, colorHex = 0x00f0ff, opacity = 0.75) {
        if (!this.isInitialized || !points || points.length < 2) return null;
        const vectors = points.map(p => latLonToVec3(p.lat, p.lon, p.altitude_km || p.alt_km || 0));
        const geo = new THREE.BufferGeometry().setFromPoints(vectors);
        const mat = new THREE.LineBasicMaterial({ color: colorHex, transparent: true, opacity });
        const line = new THREE.Line(geo, mat);
        this.scene.add(line);
        return this.trackOverlayObject(line);
    }

    createDebrisCloud(center, radiusKm, intensity = 1.0) {
        if (!this.isInitialized || !center) return null;
        const sceneRadius = Math.max(0.08, (radiusKm * EARTH_RADIUS_UNITS) / EARTH_RADIUS_KM);
        const pos = latLonToVec3(center.lat, center.lon, center.altitude_km || 0);
        const mesh = new THREE.Mesh(
            new THREE.SphereGeometry(sceneRadius, 16, 16),
            new THREE.MeshBasicMaterial({
                color: 0xff3b30,
                transparent: true,
                opacity: Math.min(0.32, 0.08 + intensity * 0.24),
                wireframe: true,
            })
        );
        mesh.position.copy(pos);
        this.scene.add(mesh);
        return this.trackOverlayObject(mesh);
    }

    createHeatPoint(cell) {
        if (!this.isInitialized || !cell) return null;
        const pos = latLonToVec3(cell.lat, cell.lon, (cell.altitude_band_km?.[0] || 0));
        const risk = Math.max(0.1, Math.min(1.0, cell.risk_score || 0));
        const mesh = new THREE.Mesh(
            new THREE.SphereGeometry(0.018 + risk * 0.055, 8, 8),
            new THREE.MeshBasicMaterial({
                color: risk > 0.7 ? 0xff3b30 : (risk > 0.35 ? 0xffcc00 : 0x00ff88),
                transparent: true,
                opacity: 0.35 + risk * 0.45,
            })
        );
        mesh.position.copy(pos);
        this.scene.add(mesh);
        return this.trackOverlayObject(mesh);
    }
}
