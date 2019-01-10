# -*- coding: utf-8 -*-

from .models import FabLabUser, UserActivityMonitor, ActivityDocument
from django.contrib.auth.models import User
from channels import Group
from .signals import circle_command
from channels.auth import channel_session_user, channel_session_user_from_http
import simplejson as json
import os

# beim connect wird der kanal der users gruppe zugeordnet und ein hallo geschickt


@channel_session_user_from_http
def ws_connect(message):
    Group('users').add(message.reply_channel)
    message.reply_channel.send({
        'text': json.dumps({
            'welcome': 'welcome to the fablab access control websocket channel'
        })
    })

# beim disconnet wird der kanal entfernt


@channel_session_user_from_http
def ws_disconnect(message):
    Group('users').discard(message.reply_channel)

# wenn eine nachricht empfangen wird erst nachsehen ob der benutzer
# angemeldet ist,
# existiert
# und ggfls superuser rechte hat


@channel_session_user
def ws_receive(message):
    try:
        user = User.objects.get(username=message.user)
        fablabuser = FabLabUser.objects.get(user=user)
    except Exception as e:
        print(
            'Websocket Nachricht Fehler! Nachricht : {} von Benutzer : {} Fehler : {}'.format(
                message.content['text'],
                message.user,
                e))
    else:
        if fablabuser.user.is_superuser:
            msg = json.loads(message.content['text'])
            if msg['cmd'] == 'switch':
                print(
                    'Websocket Nachricht erhalten : {} von Benutzer : {}'.format(
                        message.content['text'], message.user))
                msg['user'] = fablabuser.id
                # circle_command ist ein signal und wird vom mqtt script empfangen
                circle_command.send(sender='FabLabControl', message=json.dumps(msg))
            elif msg['cmd'] == 'userimage':
                import base64
                from django.core.files.base import ContentFile

                username = msg['fablabuser']
                try:
                    user = User.objects.get(username=username)
                    moduser = FabLabUser.objects.get(user=user)
                except:
                    moduser = None
                else:
                    # altes bild löschen falls vorhanden
                    if moduser.image != '':
                        image_path = os.path.join(moduser.image.path)
                        try:
                            os.unlink(image_path)
                        except:
                            pass
                    moduser.image.save(
                        'name.png', ContentFile(
                            base64.b64decode(
                                msg['data'])), save=True)
            elif msg['cmd'] == 'activityimage':
                print('got activity image...')
                import base64
                from django.core.files.base import ContentFile

                activitiy_id = msg['activity']
                try:
                    activity = UserActivityMonitor.objects.get(pk=activitiy_id)
                except:
                    activity = None
                else:
                    doc = ActivityDocument(
                        file=ContentFile(
                            base64.b64decode(
                                msg['data']),
                            'name.png'),
                        activity=activity)
                    doc.save()
