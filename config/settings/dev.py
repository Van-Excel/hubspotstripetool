import os
from .base import *

DEBUG = True

ALLOWED_HOSTS = ["*"]

if os.environ.get("USE_SQLITE") == "1":
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": os.path.join(BASE_DIR, "db.sqlite3"),
        }
    }
    CELERY_TASK_ALWAYS_EAGER = True
