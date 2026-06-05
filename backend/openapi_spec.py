from typing import Any, Dict


def build_openapi_spec() -> Dict[str, Any]:
    return {
        "openapi": "3.0.3",
        "info": {
            "title": "Collision Risk Visualizer API",
            "version": "1.0.0",
            "description": "Versioned REST API for orbital objects, conjunctions, alerts, auth, and visualization overlays.",
        },
        "servers": [{"url": "/api/v1", "description": "Version 1 API"}],
        "components": {
            "securitySchemes": {
                "bearerAuth": {"type": "http", "scheme": "bearer", "bearerFormat": "JWT"}
            }
        },
        "paths": {
            "/auth/signup": {"post": {"summary": "Create a user account", "tags": ["Auth"]}},
            "/auth/login": {"post": {"summary": "Issue an auth token", "tags": ["Auth"]}},
            "/auth/me": {"get": {"summary": "Current user profile", "tags": ["Auth"], "security": [{"bearerAuth": []}]}},
            "/profile": {"patch": {"summary": "Update user profile", "tags": ["Auth"], "security": [{"bearerAuth": []}]}},
            "/preferences": {
                "get": {"summary": "Get preferences and watched satellites", "tags": ["Users"], "security": [{"bearerAuth": []}]},
                "put": {"summary": "Update preferences and alert settings", "tags": ["Users"], "security": [{"bearerAuth": []}]},
            },
            "/watched-satellites": {
                "post": {"summary": "Add a watched satellite", "tags": ["Users"], "security": [{"bearerAuth": []}]}
            },
            "/watched-satellites/{name}": {
                "delete": {"summary": "Remove a watched satellite", "tags": ["Users"], "security": [{"bearerAuth": []}]}
            },
            "/objects": {"get": {"summary": "Live propagated orbital objects", "tags": ["Telemetry"]}},
            "/satellite": {"get": {"summary": "Satellite detail by name", "tags": ["Telemetry"]}},
            "/search": {"get": {"summary": "Search satellites by name", "tags": ["Telemetry"]}},
            "/conjunctions": {"get": {"summary": "Conjunction screening results", "tags": ["Risk"]}},
            "/stats": {"get": {"summary": "Orbital environment stats", "tags": ["Telemetry"]}},
            "/ground-visibility": {"get": {"summary": "Ground station line-of-sight links", "tags": ["Overlays"]}},
            "/maneuvers": {"get": {"summary": "ISS/Hubble maneuver predictions", "tags": ["Overlays"]}},
            "/debris-risk": {"get": {"summary": "Cascading debris risk simulation", "tags": ["Risk"]}},
            "/launches": {"get": {"summary": "Upcoming launches", "tags": ["Launches"]}},
            "/heatmap": {"get": {"summary": "Orbital congestion heatmap", "tags": ["Risk"]}},
            "/alerts/test": {"post": {"summary": "Send a test alert to current user", "tags": ["Alerts"], "security": [{"bearerAuth": []}]}},
            "/admin/cache-status": {"get": {"summary": "Cache backend status", "tags": ["Admin"], "security": [{"bearerAuth": []}]}},
        },
    }


def swagger_ui_html() -> str:
    return """
    <!doctype html>
    <html lang="en">
    <head>
      <meta charset="utf-8">
      <meta name="viewport" content="width=device-width, initial-scale=1">
      <title>Collision Risk Visualizer API Docs</title>
      <link rel="stylesheet" href="https://unpkg.com/swagger-ui-dist@5/swagger-ui.css">
    </head>
    <body>
      <div id="swagger-ui"></div>
      <script src="https://unpkg.com/swagger-ui-dist@5/swagger-ui-bundle.js"></script>
      <script>
        SwaggerUIBundle({ url: '/api/v1/openapi.json', dom_id: '#swagger-ui' });
      </script>
    </body>
    </html>
    """
