from .settings import *  # noqa
from .settings import BASE_DIR

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db_test.sqlite3",
    }
}

PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.MD5PasswordHasher",
]

CELERY_BROKER_URL = "memory://"
CELERY_RESULT_BACKEND = "db+sqlite:///results.sqlite"
