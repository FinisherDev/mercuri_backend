from celery import shared_task
from django.utils import timezone
from .utils import create_offers_for_order
from .models import Order, Offer, OfferEvent

@shared_task(bind=True, max_retries=3)
def dispatch_offers(self, order_id):
    """
        Notify drivers within 3km of the new order
    """
    try:
        order = Order.objects.get(id=order_id)
        if order.status != 'pending':
            return "Order already closed"
        create_offers_for_order(order)
        return "Offers Created"
    except Exception as e:
        self.retry(exc=e, countdown=5)

@shared_task
def expire_old_offers():
    now = timezone.now()

    Offer.objects.filter(expires_at__lt=now, accepted=False).delete()
    Order.objects.filter(expires_at__lt=now, status='pending').update(status='expired')