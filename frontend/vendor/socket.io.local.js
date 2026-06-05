/**
 * Local Socket.IO Shim (polling fallback)
 * Provides a minimal `io()` function so the UI can use the same
 * `.on()` handlers used for Socket.IO. This shim polls the backend
 * REST endpoints and emits equivalent events: 'objects', 'conjunctions', 'stats'.
 *
 * This is intentionally lightweight and only used to avoid CDN/network
 * failures during development. It does not implement the Socket.IO wire
 * protocol and is strictly a client-side polling emulation.
 */
(function (global) {
    // Loader: prefer a local vendored socket.io client, fall back to CDN,
    // and if both fail, install the polling shim as a robust fallback.
    const LOCAL_CLIENT = '/vendor/socket.io.min.js';
    const CDN_CLIENT = 'https://cdn.jsdelivr.net/npm/socket.io-client@4.5.4/dist/socket.io.min.js';

    function installShim() {
        // Original polling shim implementation (kept as fallback)
        function createSocket(baseUrl) {
            baseUrl = baseUrl || (location.protocol + '//' + (location.hostname || '127.0.0.1') + ':5000');

            const listeners = Object.create(null);
            let stopped = false;

            function emit(evt, payload) {
                const fns = listeners[evt];
                if (!fns) return;
                for (let i = 0; i < fns.length; i++) {
                    try { fns[i](payload); } catch (e) { console.warn('[socket-shim] handler error', e); }
                }
            }

            // Simulate immediate connect
            setTimeout(() => emit('connect'), 0);

            // Polling loops
            const poll = (path, evt, interval) => {
                let running = true;
                const run = async () => {
                    if (stopped || !running) return;
                    try {
                        const res = await fetch(baseUrl + path, { cache: 'no-store' });
                        if (res.ok) {
                            const j = await res.json();
                            emit(evt, j);
                        }
                    } catch (e) {
                        // non-fatal, keep polling
                    }
                    if (running) setTimeout(run, interval);
                };
                run();
                return () => { running = false; };
            };

            const stopObjs = poll('/api/objects', 'objects', 3000);
            const stopConjs = poll('/api/conjunctions', 'conjunctions', 5000);
            const stopStats = poll('/api/stats', 'stats', 5000);

            return {
                on: function (ev, cb) {
                    if (!listeners[ev]) listeners[ev] = [];
                    listeners[ev].push(cb);
                    return this;
                },
                off: function (ev, cb) {
                    if (!listeners[ev]) return this;
                    const i = listeners[ev].indexOf(cb);
                    if (i >= 0) listeners[ev].splice(i, 1);
                    return this;
                },
                emit: function () { /* noop for shim */ },
                disconnect: function () {
                    stopped = true;
                    stopObjs(); stopConjs(); stopStats();
                    emit('disconnect');
                }
            };
        }

        // Expose global `io` factory expected by the UI
        global.io = function (baseUrl) { return createSocket(baseUrl); };
        console.warn('[socket-loader] using polling shim fallback (socket.io client not available)');
    }

    function tryLoadScript(src, onload, onerror) {
        try {
            const s = document.createElement('script');
            s.src = src;
            s.async = true;
            s.onload = onload;
            s.onerror = onerror;
            document.head.appendChild(s);
            return s;
        } catch (e) {
            if (onerror) onerror(e);
            return null;
        }
    }

    // Try local file first, then CDN, then fallback to shim.
    // Do this asynchronously so the page can continue loading; ui.js will
    // retry connecting if `io` appears later.
    (function loadClient() {
        // If a global `io` is already present, nothing to do
        if (typeof global.io !== 'undefined') return;

        // Attempt to load a local vendored client
        tryLoadScript(LOCAL_CLIENT, () => {
            console.log('[socket-loader] loaded local socket.io client:', LOCAL_CLIENT);
        }, () => {
            // Local failed; try CDN
            tryLoadScript(CDN_CLIENT, () => {
                console.log('[socket-loader] loaded socket.io client from CDN');
            }, () => {
                // CDN failed — install the polling shim
                installShim();
            });
        });
    })();

})(window);
