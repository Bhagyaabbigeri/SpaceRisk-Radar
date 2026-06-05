from flask import Blueprint, g, jsonify, request

from backend.alerts import alert_dispatcher
from backend.auth_service import auth_service, require_auth, require_role
from backend.cache_layer import cache_layer
from backend.openapi_spec import build_openapi_spec, swagger_ui_html


def create_api_v1_blueprint(handlers: dict):
    bp = Blueprint("api_v1", __name__, url_prefix="/api/v1")

    @bp.route("/openapi.json")
    def openapi_json():
        return jsonify(build_openapi_spec())

    @bp.route("/docs")
    def docs():
        return swagger_ui_html()

    @bp.route("/auth/signup", methods=["POST"])
    def signup():
        payload = request.get_json(silent=True) or {}
        try:
            user = auth_service.create_user(
                payload.get("email"),
                payload.get("password"),
                payload.get("display_name", ""),
                payload.get("role", "user") if payload.get("admin_invite") == "local-dev-admin" else "user",
            )
            return jsonify({"user": user, "token": auth_service.issue_token(user)}), 201
        except ValueError as exc:
            return jsonify({"error": str(exc)}), 400

    @bp.route("/auth/login", methods=["POST"])
    def login():
        payload = request.get_json(silent=True) or {}
        user = auth_service.authenticate(payload.get("email"), payload.get("password"))
        if not user:
            return jsonify({"error": "invalid credentials"}), 401
        return jsonify({"user": user, "token": auth_service.issue_token(user), "expires_in": 8 * 60 * 60})

    @bp.route("/auth/logout", methods=["POST"])
    @require_auth
    def logout():
        return jsonify({"ok": True, "message": "discard bearer token client-side"})

    @bp.route("/auth/me")
    @require_auth
    def me():
        return jsonify({"user": g.current_user})

    @bp.route("/profile", methods=["PATCH"])
    @require_auth
    def update_profile():
        payload = request.get_json(silent=True) or {}
        user = auth_service.update_profile(g.current_user["id"], payload.get("display_name", ""))
        return jsonify({"user": user})

    @bp.route("/preferences", methods=["GET"])
    @require_auth
    def get_preferences():
        return jsonify(auth_service.get_preferences(g.current_user["id"]))

    @bp.route("/preferences", methods=["PUT"])
    @require_auth
    def update_preferences():
        payload = request.get_json(silent=True) or {}
        return jsonify(auth_service.update_preferences(g.current_user["id"], payload))

    @bp.route("/watched-satellites", methods=["POST"])
    @require_auth
    def add_watched_satellite():
        payload = request.get_json(silent=True) or {}
        try:
            return jsonify(auth_service.add_watched_satellite(g.current_user["id"], payload.get("satellite_name")))
        except ValueError as exc:
            return jsonify({"error": str(exc)}), 400

    @bp.route("/watched-satellites/<path:name>", methods=["DELETE"])
    @require_auth
    def remove_watched_satellite(name):
        return jsonify(auth_service.remove_watched_satellite(g.current_user["id"], name))

    # Versioned aliases for existing public telemetry and overlay APIs.
    for path, endpoint_name in {
        "/objects": "objects",
        "/satellite": "satellite",
        "/search": "search",
        "/conjunctions": "conjunctions",
        "/stats": "stats",
        "/ground-visibility": "ground_visibility",
        "/maneuvers": "maneuvers",
        "/debris-risk": "debris_risk",
        "/launches": "launches",
        "/heatmap": "heatmap",
    }.items():
        bp.add_url_rule(path, f"v1_{endpoint_name}", handlers[endpoint_name], methods=["GET"])

    @bp.route("/alerts/test", methods=["POST"])
    @require_auth
    def test_alert():
        payload = request.get_json(silent=True) or {}
        event = payload.get("event") or {
            "sat1": "DEMO-SAT-1",
            "sat2": "DEMO-DEBRIS-1",
            "distance_km": 12.5,
        }
        result = alert_dispatcher.dispatch_conjunction_alerts([event])
        return jsonify(result)

    @bp.route("/admin/cache-status")
    @require_role("admin")
    def cache_status():
        return jsonify(cache_layer.status())

    return bp
