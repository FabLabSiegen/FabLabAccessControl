from __future__ import unicode_literals

from django.apps import AppConfig


class FabLabControl(AppConfig):
    name = 'fablabcontrol'

    def ready(self):
        import fablabcontrol.signals
