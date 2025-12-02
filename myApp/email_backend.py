import ssl
from django.core.mail.backends.smtp import EmailBackend


class UnverifiedEmailBackend(EmailBackend):
    """
    A custom email backend that ignores SSL certificate verification.
    Use this ONLY for development/testing inside Docker if you have Antivirus/VPN issues.
    """
    def _get_ssl_context(self):
        # This tells Python: "Don't verify the certificate, just trust it."
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        return ctx

    def open(self):
        # We override the open method to inject our relaxed SSL context
        self.ssl_context = self._get_ssl_context()
        return super().open()