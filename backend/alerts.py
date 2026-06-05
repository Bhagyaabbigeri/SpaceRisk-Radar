import json
import logging
import os
import smtplib
import threading
import time
import urllib.request
from email.message import EmailMessage
from typing import Any, Callable, Dict, Iterable

from backend.auth_service import auth_service


logger = logging.getLogger(__name__)


class AlertDispatcher:
    def __init__(self):
        self.smtp_host = os.environ.get("CRV_SMTP_HOST")
        self.smtp_port = int(os.environ.get("CRV_SMTP_PORT", "587"))
        self.smtp_user = os.environ.get("CRV_SMTP_USER")
        self.smtp_password = os.environ.get("CRV_SMTP_PASSWORD")
        self.sender = os.environ.get("CRV_ALERT_FROM", self.smtp_user or "alerts@collision-risk.local")

    def dispatch_conjunction_alerts(self, conjunctions: Iterable[Dict[str, Any]]) -> Dict[str, Any]:
        events = [c for c in conjunctions if float(c.get("distance_km") or 999999.0) <= 50.0]
        if not events:
            return {"sent_email": 0, "sent_webhook": 0, "event_count": 0}

        sent_email = 0
        sent_webhook = 0
        for user in auth_service.users_for_alerts():
            threshold = float(user.get("alert_threshold_km") or 50.0)
            matching = [e for e in events if float(e.get("distance_km") or 999999.0) <= threshold]
            if not matching:
                continue
            if user.get("email_alerts_enabled"):
                sent_email += 1 if self._send_email(user["email"], matching) else 0
            if user.get("webhook_url"):
                sent_webhook += 1 if self._send_webhook(user["webhook_url"], matching) else 0
        return {"sent_email": sent_email, "sent_webhook": sent_webhook, "event_count": len(events)}

    def _send_email(self, recipient: str, events: list[Dict[str, Any]]) -> bool:
        if not self.smtp_host:
            logger.info(f"Email alert dry-run for {recipient}: {len(events)} events")
            return False
        try:
            msg = EmailMessage()
            msg["From"] = self.sender
            msg["To"] = recipient
            msg["Subject"] = f"Collision Risk Alert: {len(events)} high-risk event(s)"
            lines = [
                f"{e.get('sat1') or e.get('obj1')} vs {e.get('sat2') or e.get('obj2')}: {e.get('distance_km')} km"
                for e in events[:10]
            ]
            msg.set_content("\n".join(lines))
            with smtplib.SMTP(self.smtp_host, self.smtp_port, timeout=10) as smtp:
                smtp.starttls()
                if self.smtp_user and self.smtp_password:
                    smtp.login(self.smtp_user, self.smtp_password)
                smtp.send_message(msg)
            return True
        except Exception as exc:
            logger.warning(f"Email alert failed for {recipient}: {exc}")
            return False

    def _send_webhook(self, url: str, events: list[Dict[str, Any]]) -> bool:
        try:
            body = json.dumps({"type": "collision_risk", "events": events[:10]}).encode("utf-8")
            req = urllib.request.Request(
                url,
                data=body,
                headers={"Content-Type": "application/json", "User-Agent": "Collision-Risk-Visualizer/1.0"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=10) as resp:
                return 200 <= resp.status < 300
        except Exception as exc:
            logger.warning(f"Webhook alert failed for {url}: {exc}")
            return False


class AlertScheduler:
    def __init__(self, dispatcher: AlertDispatcher):
        self.dispatcher = dispatcher
        self.thread = None
        self.stop_event = threading.Event()

    def start(self, event_provider: Callable[[], list[Dict[str, Any]]], interval_seconds: int = 300) -> None:
        if self.thread and self.thread.is_alive():
            return

        def loop():
            logger.info("Alert scheduler started.")
            while not self.stop_event.is_set():
                try:
                    self.dispatcher.dispatch_conjunction_alerts(event_provider())
                except Exception as exc:
                    logger.warning(f"Alert scheduler cycle failed: {exc}")
                self.stop_event.wait(interval_seconds)

        self.thread = threading.Thread(target=loop, daemon=True)
        self.thread.start()


alert_dispatcher = AlertDispatcher()
alert_scheduler = AlertScheduler(alert_dispatcher)
