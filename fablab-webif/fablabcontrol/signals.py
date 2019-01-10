import django.dispatch
from django.db.models.signals import post_save
from django.dispatch import receiver
from.models import PlugwiseCircle

# wird geschickt wenn websocket nachricht empfangen und
# vom mqtt script empfangen
circle_command = django.dispatch.Signal(providing_args=["message"])

@receiver(post_save, sender=PlugwiseCircle)
def update_circle(sender, instance, **kwargs):
    import simplejson as json

    circle_command.send(sender='Model', message=json.dumps({'cmd': 'save', 'circle': instance.id}))
