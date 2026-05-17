"""
Firebase Cloud Messaging: send notifications to hub (e.g. new lead).
Uses Firebase Admin SDK. Configure via Django settings:
- FIREBASE_SERVICE_ACCOUNT_JSON: path to service account JSON file (from .env via config()), or
  set GOOGLE_APPLICATION_CREDENTIALS in env for compatibility.
If not set, all functions no-op.
"""
import json
import logging
import os

logger = logging.getLogger(__name__)

FCM_TOPIC_LEADS = "hub_leads"
_firebase_app = None


def _get_firebase_app():
    global _firebase_app
    if _firebase_app is not None:
        return _firebase_app
    try:
        import firebase_admin
        from firebase_admin import credentials
    except ImportError:
        print("Firebase Admin: firebase-admin not installed. pip install firebase-admin")
        return None
    from django.conf import settings
    path = getattr(settings, "FIREBASE_SERVICE_ACCOUNT_JSON", None) or os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
    if not path:
        print("Firebase Admin: FIREBASE_SERVICE_ACCOUNT_JSON not set in .env")
        return None
    path = str(path).strip()
    # Resolve relative path against Django project root
    if not os.path.isabs(path) and not path.startswith("{"):
        path = os.path.join(settings.BASE_DIR, path)
    # File path
    if os.path.isfile(path):
        try:
            cred = credentials.Certificate(path)
            _firebase_app = firebase_admin.initialize_app(cred)
            return _firebase_app
        except Exception as e:
            print("Firebase Admin init failed: %s", e)
            return None
    # Inline JSON
    if path.startswith("{"):
        try:
            cred = credentials.Certificate(json.loads(path))
            _firebase_app = firebase_admin.initialize_app(cred)
            return _firebase_app
        except (json.JSONDecodeError, ValueError, Exception) as e:
            print("Firebase Admin init (inline JSON) failed: %s", e)
            return None
    print("Firebase Admin: file not found: %s", path)
    return None


def send_lead_notification(lead):
    """
    Send FCM notification to topic hub_leads when a new lead is created.
    lead: Lead instance with name, email, id.
    """
    print("lead: ", lead)
    app = _get_firebase_app()
    print("app: ", app)
    if not app:
        print("FCM: Firebase not initialized, skipping new-lead notification for lead %s", lead.id)
        return
    try:
        from firebase_admin import messaging
        body = f"{lead.name} — {lead.email}"
        message = messaging.Message(
            notification=messaging.Notification(
                title="New lead",
                body=body,
            ),
            data={
                "title": "New lead",
                "body": body,
                "leadId": str(lead.id),
            },
            topic=FCM_TOPIC_LEADS,
        )
        messaging.send(message)
        print("message: ", message)
        print("status: ", messaging.send(message))
        print("FCM: Sent new-lead notification for lead %s (%s)", lead.id, lead.name)
    except Exception as e:
        print("FCM send_lead_notification failed: %s", e)


def subscribe_token_to_topic(token: str, topic: str = FCM_TOPIC_LEADS) -> bool:
    """Subscribe an FCM registration token to a topic (e.g. hub_leads). Returns True on success."""
    app = _get_firebase_app()
    if not app:
        return False
    try:
        from firebase_admin import messaging
        messaging.subscribe_to_topic([token], topic)
        return True
    except Exception as e:
        print("FCM subscribe_token_to_topic failed: %s", e)
        return False
