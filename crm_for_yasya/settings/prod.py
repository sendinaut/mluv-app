from crm_for_yasya.settings.base import *

DEBUG = False

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.environ["POSTGRES_DB"],
        "USER": os.environ["POSTGRES_USER"],
        "PASSWORD": os.environ["POSTGRES_PASSWORD"],
        "HOST": os.environ["POSTGRES_HOST"],
        "PORT": os.environ["POSTGRES_PORT"],
    }
}

Q_CLUSTER = {
    "name": "crm_queue",
    "workers": 2,
    "timeout": 180,
    "retry": 180,
    "orm": "default",
}
