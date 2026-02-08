import firebase_admin
from firebase_admin import credentials, messaging
from django.conf import settings

firebase_app = None

def get_firebase_app():
    global firebase_app
    if not firebase_app:
        cred = credentials.Certificate(settings.FIREBASE_CREDENTIALS)
        firebase_app = firebase_admin.initialize_app(cred)
    return firebase_app

def send_push_notification(token, title, body, data=None):
    get_firebase_app()

    message = messaging.Message(
        notification = messaging.Notification(
            title = title,
            body = body
        ),
        token = token,
        data = {key: str(value) for key, value in (data or {}).items()}
    )
    response = messaging.send(message)
    return response