from django.apps import AppConfig


class AdmissionConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'admission'
    
    def ready(self):
        import core.signals
