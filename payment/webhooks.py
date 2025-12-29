import stripe
from django.conf import settings
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
import stripe.error
from order.models import Order
from cart.models import Cart
from .task import send_successful_payment_email


@csrf_exempt
def stripe_webhook(request):
    payload = request.body
    sig_header = request.META.get("HTTP_STRIPE_SIGNATURE")
    if sig_header is None:
        return HttpResponse(status=400)
    event = None

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
    except ValueError:
        # Invalid payload
        return HttpResponse(status=400)
    except stripe.error.SignatureVerificationError:
        return HttpResponse(status=400)

    if event.type == "checkout.session.completed":
        session = event.data.object
        if session.mode == "payment" and session.payment_status == "paid":
            try:
                order = Order.objects.get(id=session.client_reference_id)
            except Order.DoesNotExist:
                return HttpResponse(status=404)

            # add the stripe_id and mark the order as paid
            order.paid = True
            order.stripe_id = session.payment_intent
            order.save()

            # Send recipt via email
            send_successful_payment_email.delay(order.id)

            # recude the books from inventory
            for item in order.items.all():
                item.book.stock -= item.quantity
                item.book.save()

            # clear cart
            cart = Cart.objects.filter(user=order.user).first()
            if cart:
                cart.items.all().delete()

    return HttpResponse(status=200)
