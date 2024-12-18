from oscar.core.application import OscarConfig


class CommunicationConfig(OscarConfig):
    label = "communication"
    name = "oscar.apps.communication"
    verbose_name = "Уведомления"
    
    def ready(self):
        from . import receivers
