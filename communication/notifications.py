from firebase_admin import messaging
from .models import FCMDevice

def send_fcm_notification(user, title, body, data=None):
    """Send FCM notification to all user's devices"""
    devices = FCMDevice.objects.filter(user=user, is_active=True)
    
    if not devices.exists():
        return
    
    tokens = [device.registration_token for device in devices]
    
    message = messaging.MulticastMessage(
        notification=messaging.Notification(
            title=title,
            body=body,
        ),
        data=data or {},
        tokens=tokens,
    )
    
    try:
        response = messaging.send_multicast(message)
        
        # Deactivate failed tokens
        if response.failure_count > 0:
            for idx, resp in enumerate(response.responses):
                if not resp.success:
                    device = devices[idx]
                    device.is_active = False
                    device.save()
        
        return response
    except Exception as e:
        print(f"Error sending FCM notification: {e}")
        return None