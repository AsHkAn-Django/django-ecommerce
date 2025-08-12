from django.core.mail import EmailMessage
from django.contrib.staticfiles import finders
from django.template.loader import render_to_string
from django.conf import settings
from django.core.files.base import ContentFile

from celery import shared_task
from order.models import Order

import weasyprint
import os
import qrcode
from io import BytesIO


# Change this to your actual production domain when deploying
DOMAIN = 'http://127.0.0.1:8000/'


@shared_task
def send_successful_payment_email(order_id):
    # Fetch the order instance
    order = Order.objects.get(id=order_id)

    # Prepare email
    subject = f'Book Store - Recipe no. {order_id}'
    message = 'Your Recipe and QR code have been attached to this email.'
    email = EmailMessage(subject, message, from_email=None, to=[order.email])


    # -------------- PDF GENERATION -----------------
    # Render HTML template to string for PDF content
    html = render_to_string('order/pdf.html', {'order': order})

    # Ensure the PDF output directory exists
    pdf_output_dir = os.path.join(settings.MEDIA_ROOT, 'recipts')
    os.makedirs(pdf_output_dir, exist_ok=True)

    # Define PDF filename
    pdf_filename = f'recipt_order_{order_id}.pdf'
    pdf_path = os.path.join(pdf_output_dir, pdf_filename)

    # Load CSS for PDF if any
    stylesheets = [weasyprint.CSS(finders.find('css/pdf.css'))]

    # Generate PDF bytes
    pdf_bytes = weasyprint.HTML(string=html).write_pdf(stylesheets=stylesheets)

    # Save PDF file to model (and optionally to disk if needed)
    order.recipt_file.save(pdf_filename, ContentFile(pdf_bytes))


    # -------------- QR CODE GENERATION -------------
    # Generate the absolute URL to the recipt PDF
    pdf_url = DOMAIN + settings.MEDIA_URL + 'recipts/' + pdf_filename

    # Create QR code for that URL
    qr = qrcode.make(pdf_url)

    # Save QR code image to a BytesIO buffer
    qr_io = BytesIO()
    qr.save(qr_io)
    qr_io.seek(0)  # Reset pointer before saving

    # Save QR code image to model
    order.qr_file.save(f'qr_{order_id}.png', ContentFile(qr_io.read()))

    # Reset pointer again to reuse the same stream for attachment
    qr_io.seek(0)

    # Save order instance
    order.save()


    # ------------ ATTACH FILES TO EMAIL ------------
    email.attach(pdf_filename, pdf_bytes, 'application/pdf')
    email.attach(f'qr_{order.id}.png', qr_io.read(), 'image/png')

    # Send email
    email.send()
