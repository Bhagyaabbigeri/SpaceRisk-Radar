/**
 * Minimal Ionicons replacement for local development.
 * Defines a lightweight <ion-icon name="..."></ion-icon> custom element
 * that renders a small set of SVGs used by the UI. Icons use currentColor
 * so they follow surrounding text color and sizing.
 */
(function () {
    const icons = {
        'add': '<svg viewBox="0 0 24 24" width="1em" height="1em" fill="currentColor" aria-hidden="true"><path d="M11 11V3h2v8h8v2h-8v8h-2v-8H3v-2z"/></svg>',
        'remove': '<svg viewBox="0 0 24 24" width="1em" height="1em" fill="currentColor" aria-hidden="true"><path d="M5 11h14v2H5z"/></svg>',
        'sync': '<svg viewBox="0 0 24 24" width="1em" height="1em" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M21 12a9 9 0 10-3.1 6.3L21 21v-4.7"/><path d="M3 12a9 9 0 003.1-6.3L3 3v4.7"/></svg>',
        'planet': '<svg viewBox="0 0 24 24" width="1em" height="1em" fill="currentColor" aria-hidden="true"><circle cx="12" cy="12" r="4"/><path d="M2 12c3-4 9-6 14-6s11 2 14 6c-3 4-9 6-14 6S5 16 2 12z" fill-opacity="0.12"/></svg>',
        'radar': '<svg viewBox="0 0 24 24" width="1em" height="1em" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="12" cy="12" r="10"/><path d="M12 6v6l4 2"/></svg>',
        'warning': '<svg viewBox="0 0 24 24" width="1em" height="1em" fill="currentColor" aria-hidden="true"><path d="M10.29 3.86L1.82 18a2 2 0 001.71 3h16.94a2 2 0 001.71-3L13.71 3.86a2 2 0 00-3.42 0zM11 10h2v4h-2zm0 6h2v2h-2z"/></svg>',
        'options': '<svg viewBox="0 0 24 24" width="1em" height="1em" fill="currentColor" aria-hidden="true"><path d="M19.4 15a1.65 1.65 0 00.33 1.82l.06.06a2 2 0 01-2.83 2.83l-.06-.06a1.65 1.65 0 00-1.82-.33 1.65 1.65 0 00-1 1.51V21a2 2 0 01-4 0v-.09a1.65 1.65 0 00-1-1.51 1.65 1.65 0 00-1.82.33l-.06.06A2 2 0 015.27 16.9l.06-.06A1.65 1.65 0 005.66 15 1.65 1.65 0 004.15 13.5H4a2 2 0 010-4h.15A1.65 1.65 0 005.66 8.5a1.65 1.65 0 00.33-1.82L5.93 6.62A2 2 0 018.76 3.79l.06.06A1.65 1.65 0 0011 4.18 1.65 1.65 0 0012.51 3h.98A1.65 1.65 0 0015 4.18a1.65 1.65 0 001.82.33l.06-.06A2 2 0 0118.73 7.1l-.06.06A1.65 1.65 0 0018.34 9a1.65 1.65 0 00.33 1.82L19.4 12.5a1.65 1.65 0 000 2.5z"/></svg>',
        'analytics': '<svg viewBox="0 0 24 24" width="1em" height="1em" fill="currentColor" aria-hidden="true"><rect x="3" y="11" width="4" height="10"/><rect x="10" y="6" width="4" height="15"/><rect x="17" y="2" width="4" height="19"/></svg>',
        'barcode': '<svg viewBox="0 0 24 24" width="1em" height="1em" fill="currentColor" aria-hidden="true"><rect x="2" y="4" width="2" height="16"/><rect x="6" y="4" width="1" height="16"/><rect x="9" y="4" width="2" height="16"/><rect x="13" y="4" width="1" height="16"/><rect x="16" y="4" width="2" height="16"/><rect x="20" y="4" width="1" height="16"/></svg>',
        'radio-outline': '<svg viewBox="0 0 24 24" width="1em" height="1em" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="2" y="7" width="20" height="12" rx="2"/><path d="M16 3v4"/></svg>',
        'flash': '<svg viewBox="0 0 24 24" width="1em" height="1em" fill="currentColor" aria-hidden="true"><path d="M13 2L3 14h7l-1 8 10-12h-7z"/></svg>',
        'checkmark-circle-outline': '<svg viewBox="0 0 24 24" width="1em" height="1em" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="12" cy="12" r="9"/><path d="M9 12l2 2 4-4"/></svg>'
        ,
        // Additional common icons for local development
        'menu': '<svg viewBox="0 0 24 24" width="1em" height="1em" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M3 6h18M3 12h18M3 18h18"/></svg>',
        'search': '<svg viewBox="0 0 24 24" width="1em" height="1em" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="11" cy="11" r="7"/><path d="M21 21l-4.35-4.35"/></svg>',
        'close': '<svg viewBox="0 0 24 24" width="1em" height="1em" fill="currentColor" aria-hidden="true"><path d="M18.3 5.71L12 12l6.3 6.29-1.41 1.42L10.59 13.41 4.29 19.71 2.88 18.29 9.18 12 2.88 5.71 4.29 4.29 10.59 10.59 16.88 4.29z"/></svg>',
        'close-circle-outline': '<svg viewBox="0 0 24 24" width="1em" height="1em" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="12" cy="12" r="9"/><path d="M15 9L9 15M9 9l6 6"/></svg>',
        'chevron-down': '<svg viewBox="0 0 24 24" width="1em" height="1em" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M6 9l6 6 6-6"/></svg>',
        'trash': '<svg viewBox="0 0 24 24" width="1em" height="1em" fill="currentColor" aria-hidden="true"><path d="M3 6h18M8 6v12a2 2 0 002 2h4a2 2 0 002-2V6"/></svg>',
        'eye': '<svg viewBox="0 0 24 24" width="1em" height="1em" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M1 12s4-7 11-7 11 7 11 7-4 7-11 7S1 12 1 12z"/><circle cx="12" cy="12" r="3"/></svg>',
        'eye-off': '<svg viewBox="0 0 24 24" width="1em" height="1em" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M17.94 17.94A10.94 10.94 0 0112 20c-7 0-11-8-11-8a21.18 21.18 0 015.12-6.07"/><line x1="1" y1="1" x2="23" y2="23"/></svg>',
        'help-circle-outline': '<svg viewBox="0 0 24 24" width="1em" height="1em" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="12" cy="12" r="9"/><path d="M9.09 9a3 3 0 015.83.79c0 1.5-2 2.5-2 3.5M12 17h.01"/></svg>',
        'information-circle-outline': '<svg viewBox="0 0 24 24" width="1em" height="1em" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="12" cy="12" r="9"/><path d="M12 8h.01M11 12h1v4h1"/></svg>',
        'play': '<svg viewBox="0 0 24 24" width="1em" height="1em" fill="currentColor" aria-hidden="true"><path d="M5 3v18l15-9L5 3z"/></svg>',
        'pause': '<svg viewBox="0 0 24 24" width="1em" height="1em" fill="currentColor" aria-hidden="true"><path d="M6 4h4v16H6zM14 4h4v16h-4z"/></svg>'
    };

    const style = document.createElement('style');
    style.textContent = 'ion-icon{display:inline-block;vertical-align:middle;font-size:1em;color:inherit;line-height:1}ion-icon svg{width:1em;height:1em;display:block}';
    document.head.appendChild(style);

    class IonIcon extends HTMLElement {
        connectedCallback() {
            const name = (this.getAttribute('name') || '').trim();
            const svg = icons[name] || '<svg viewBox="0 0 24 24" width="1em" height="1em" fill="currentColor" aria-hidden="true"><circle cx="12" cy="12" r="10"/></svg>';
            this.innerHTML = svg;
            // allow styling via class or inline styles
        }
    }

    if (!customElements.get('ion-icon')) {
        customElements.define('ion-icon', IonIcon);
    }
})();
