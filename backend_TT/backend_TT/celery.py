from __future__ import absolute_import, unicode_literals
import os
from celery import Celery

# Establece el módulo de configuración de Django para Celery
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend_TT.settings')

app = Celery('backend_TT')

# Cargar configuración de Celery desde settings.py
app.config_from_object('django.conf:settings', namespace='CELERY')

# Detectar tareas automáticamente en apps registradas
app.autodiscover_tasks()

@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')
