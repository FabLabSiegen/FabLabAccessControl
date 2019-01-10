# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import paho.mqtt.client as mqtt
import threading
import datetime, time


MQTT_HOST = '127.0.0.1'
MQTT_PORT = 1883
# WARNING add credentials
MQTT_USER = ''
MQTT_PASS = ''


#Open Dash is used for logging statistics about energy consumption
OPENDASH_MQTT_HOST = ''
OPENDASH_MQTT_PORT = 1883
# WARNING add credentials
OPENDASH_MQTT_USER = ''
OPENDASH_MQTT_PASS = ''


PLUGWISE_2_PY = '/root/Code/FabLabAccessControl/Plugwise-2-py'

# Topics
# FabLab WebIf
# FabLab/{esp_mac}/cmd/ {uuid} no-retain subscribe
# FabLab/{esp_mac}/status/ {uuid} retain publish

# FabLab ESP
# FabLab/{esp_mac}/cmd/ {uuid} no-retain publish
# FabLab/{esp_mac}/status/ {uuid} retain subscribe

# json message
# {'cmd':'command','data':'information'}

class fablabcontrolThread(threading.Thread):
    def __init__(self, event):
        threading.Thread.__init__(self)

        self.stop_event = event

        self.mqttc = None
        self.opendash_mqttc = None

    def run(self):
        print("Starte FabLabControl Thread, warte auf Django....")
        time.sleep(5.0)
        # callback funktion mit django signal verbinden
        from .signals import circle_command
        circle_command.connect(self.signal_callback)

        # mqtt client starten
        self.mqttc = mqtt.Client()
        self.mqttc.username_pw_set(MQTT_USER, password=MQTT_PASS)
        self.mqttc.on_connect = self.on_mqtt_connect
        self.mqttc.on_disconnect = self.on_mqtt_disconnect
        self.mqttc.on_message = self.on_mqtt_message
        self.mqttc.connect(MQTT_HOST, MQTT_PORT, 60)

        self.opendash_mqttc = mqtt.Client()
        self.opendash_mqttc.username_pw_set(OPENDASH_MQTT_USER, password=OPENDASH_MQTT_PASS)
        self.opendash_mqttc.on_connect = self.on_opendash_mqttc_connect
        self.opendash_mqttc.on_disconnect = self.on_opendash_mqttc_disconnect
        self.opendash_mqttc.connect(OPENDASH_MQTT_HOST, OPENDASH_MQTT_PORT, 60)

        try:
            while not self.stop_event.wait(0.2):
                self.mqttc.loop()
                self.opendash_mqttc.loop()
        finally:
            self.mqttc.disconnect()
            self.opendash_mqttc.disconnect()



    def on_opendash_mqttc_connect(self, client, userdata, flags, rc):
        if int(rc) != 0:
            if int(rc) == -4:
                print("MQTT_CONNECTION_TIMEOUT")
            elif int(rc) == -3:
                print("MQTT_CONNECTION_LOST")
            elif int(rc) == -2:
                print("MQTT_CONNECT_FAILED")
            elif int(rc) == 1:
                print("MQTT_CONNECT_BAD_PROTOCOL")
            elif int(rc) == 2:
                print("MQTT_CONNECT_BAD_CLIENT_ID")
            elif int(rc) == 3:
                print("MQTT_CONNECT_UNAVAILABLE")
            elif int(rc) == 4:
                print("MQTT_CONNECT_BAD_CREDENTIALS")
            elif int(rc) == 5:
                print("MQTT_CONNECT_UNAUTHORIZED")
        else:
            print("Mit OpenDash MQTT Server verbunden...")



    def on_opendash_mqttc_disconnect(self, client, userdata, rc):
        self.opendash_mqttc.reconnect()
        if rc != 0:
            print("OpenDash MQTT Verbindung verloren...")




    def on_mqtt_connect(self, client, userdata, flags, rc):
        if int(rc) != 0:
            if int(rc) == -4:
                print("MQTT_CONNECTION_TIMEOUT")
            elif int(rc) == -3:
                print("MQTT_CONNECTION_LOST")
            elif int(rc) == -2:
                print("MQTT_CONNECT_FAILED")
            elif int(rc) == 1:
                print("MQTT_CONNECT_BAD_PROTOCOL")
            elif int(rc) == 2:
                print("MQTT_CONNECT_BAD_CLIENT_ID")
            elif int(rc) == 3:
                print("MQTT_CONNECT_UNAVAILABLE")
            elif int(rc) == 4:
                print("MQTT_CONNECT_BAD_CREDENTIALS")
            elif int(rc) == 5:
                print("MQTT_CONNECT_UNAUTHORIZED")
        else:
            print("Mit MQTT Server verbunden...")
            client.subscribe("plugwise2py/#", 2)
            client.subscribe("FabLab/+/cmd", 2)
            # django.setup()



    def on_mqtt_disconnect(self, client, userdata, rc):
        self.mqttc.reconnect()
        if rc != 0:
            print("MQTT Verbindung verloren...")



    def on_mqtt_message(self, client, userdata, msg):
        import json
        from .models import PlugwiseCircle, EnergyMonitor
        from channels import Group
        import datetime

        print("MQTT Nachricht empfangen " + msg.topic + " " + msg.payload.decode('UTF-8'))

        try:
            topic = msg.topic.split('/')
            data = json.loads(msg.payload.decode('UTF-8'))

            if str(topic[0]) == "FabLab" and str(topic[2]) == "cmd":
                if data["cmd"] == "1":
                    print("ESP " +
                          str(topic[1]) +
                          " will anmelden..." +
                          msg.payload.decode('UTF-8'))
                    self.login(str(topic[1]), data)
                elif data["cmd"] == "3":
                    print("ESP " +
                          str(topic[1]) +
                          " will abmelden..." +
                          msg.payload.decode('UTF-8'))
                    self.logout(str(topic[1]), data)

            elif str(topic[0]) == "plugwise2py":
                try:
                    circle = PlugwiseCircle.objects.get(mac=data["mac"])
                    machine = circle.machine
                except Exception:
                    circle = None
                    machine = None

                if not circle and str(topic[1]) != "cmd":
                    fehlertext = u"Circle %s nicht im System gefunden!" % data["mac"]
                    print(
                            fehlertext +
                            "\n" +
                            msg.topic +
                            "\n" +
                            msg.payload.decode('UTF-8') +
                            "\n\n")
                    Group('users').send({
                        'text': json.dumps({
                            'type': 'error',
                            'text': fehlertext
                        })
                    })
                elif not machine and str(topic[1]) != "cmd":
                    fehlertext = u"Circle %s keiner Maschine zugeordnet!" % data["mac"]
                    print(
                            fehlertext +
                            "\n" +
                            msg.topic +
                            "\n" +
                            msg.payload.decode('UTF-8') +
                            "\n\n")
                #            Group('users').send({
                #                'text': json.dumps({
                #                'type': 'error',
                #                'text': fehlertext
                #                })
                #            })
                else:
                    if str(topic[1]) == 'state':
                        if str(topic[2]) == 'power':
                            # print ("Maschine " + machine.name + " verbraucht grade %f") % (data["power"])
                            Group('users').send({
                                'text': json.dumps({
                                    'type': 'power',
                                    'circle': circle.id,
                                    'machine': machine.id,
                                    'power': data["power"],
                                })
                            })

                            #print("Sende Energiedaten an OpenDash....")
                            # print('{ "id" : "owcore.fablab.' + circle.mac + '", "user" : "test@fablab.de", "parent" : [], "meta" : {}, "name" : "' + machine.name + '", "icon" : "Icons/smarthome/default_18.png", "valueTypes" : [{"name" : "Verbrauch in kW","type" : "Number", "unit" : "kW"}],"values" : [{"date" : ' + str(int(data["ts"]) * 1000) + ',"value" : [' + str(data["energy"]) + ']}]}')
                            self.opendash_mqttc.publish("/fablab" + circle.mac,
                                                   '{ "id" : "owcore.fablab.' + circle.mac + '", "user" : "test@fablab.de", "parent" : [], "meta" : {}, "name" : "' + machine.name + '", "icon" : "Icons/smarthome/default_18.png", "valueTypes" : [{"name" : "Aktueller Verbrauch in W","type" : "Number", "unit" : "W"}],"values" : [{"date" : ' + str(
                                                       int(data["ts"]) * 1000) + ',"value" : [' + str(
                                                       data["power"]) + ']}]}', 2, False)

                            # wenns strom verbraucht obwohl es aus sein sollte....
                            # funktioniert nur wenn monitoring aktiviert
                            if not circle.always_on and not machine.user and data["power"] > 0:
                                fehlertext = u"Maschine %s sollte aus sein, verbraucht aber Energie!" % machine.name
                                print(fehlertext)
                                # muss man an und aus schalten weil plugwise2py das sonst
                                # nicht rafft
                                for circle in machine.circles.all():
                                    self.mqttc.publish(
                                        "plugwise2py/cmd/switch/" +
                                        circle.mac,
                                        '{"mac":"","cmd":"switch","val":"on"}',
                                        2,
                                        False)
                                    self.mqttc.publish(
                                        "plugwise2py/cmd/switch/" +
                                        circle.mac,
                                        '{"mac":"","cmd":"switch","val":"off"}',
                                        2,
                                        False)

                                Group('users').send({
                                    'text': json.dumps({
                                        'type': 'error',
                                        'text': fehlertext
                                    })
                                })

                        elif str(topic[2]) == "energy":
                            # print ("Maschine " + machine.name + " verbrauchte Energie in %d min : %f") % (data["interval"], data["energy"])
                            if data["energy"] > 0:
                                energy = EnergyMonitor(
                                    date=datetime.datetime.fromtimestamp(
                                        data["ts"]),
                                    power=data["energy"],
                                    interval=circle.loginterval,
                                    machine=machine,
                                    circle=circle)
                                energy.save()

                            #print("Sende Energiedaten an OpenDash....")
                            # print('{ "id" : "owcore.fablab.' + circle.mac + '", "user" : "test@fablab.de", "parent" : [], "meta" : {}, "name" : "' + machine.name + '", "icon" : "Icons/smarthome/default_18.png", "valueTypes" : [{"name" : "Verbrauch in kW","type" : "Number", "unit" : "kW"}],"values" : [{"date" : ' + str(int(data["ts"]) * 1000) + ',"value" : [' + str(data["energy"]) + ']}]}')
                            self.opendash_mqttc.publish("/fablab" + circle.mac,
                                                   '{ "id" : "owcore.fablab.' + circle.mac + '", "user" : "test@fablab.de", "parent" : [], "meta" : {}, "name" : "' + machine.name + '", "icon" : "Icons/smarthome/default_18.png", "valueTypes" : [{"name" : "Verbrauch in kW","type" : "Number", "unit" : "kW"}],"values" : [{"date" : ' + str(
                                                       int(data["ts"]) * 1000) + ',"value" : [' + str(
                                                       data["energy"]) + ']}]}', 2, False)

                        elif str(topic[2]) == "circle":
                            if 'online' in data and data['online'] == False:
                                fehlertext = u"Circle %s von Maschine %s ist nicht mehr erreichbar!" % (
                                    circle.mac, circle.machine.name)
                                print(fehlertext)
                                circle.status = "Offline"
                                circle.save()
                                Group('users').send({
                                    'text': json.dumps({
                                        'type': 'circle',
                                        'circle': circle.id,
                                        'machine': machine.id,
                                        'switch': 'Offline',
                                    })
                                })
                                Group('users').send({
                                    'text': json.dumps({
                                        'type': 'error',
                                        'text': fehlertext
                                    })
                                })
                            elif 'online' in data and data['online'] == True:
                                if circle.status == "Offline":
                                    # maschine hatte verbindung verloren und ist jetzt wieder
                                    # online
                                    print(
                                            "Circle %s von Maschine %s ist wieder erreichbar und %s" %
                                            (circle.mac, machine.name, data["switch"]))
                                    circle.status = data["switch"]
                                    circle.save()
                                    Group('users').send({
                                        'text': json.dumps({
                                            'type': 'circle',
                                            'circle': circle.id,
                                            'machine': machine.id,
                                            'switch': data["switch"],
                                        })
                                    })
                                    # wenn der circle wieder online geht ist er evtl an obwohl es aus sein sollte
                                    # data["switch"] steht auf dem wert de der circle vor dem
                                    # verbindungsverlust hatte!
                                    if not circle.always_on and (
                                            data["switch"] == "off" or not machine.user):
                                        # muss man an und aus schalten weil plugwise2py das
                                        # sonst nicht rafft...denkt der ist off und sendet
                                        # deshalb kein off signal
                                        for circle in machine.circles.all():
                                            self.mqttc.publish(
                                                "plugwise2py/cmd/switch/" + circle.mac,
                                                '{"mac":"","cmd":"switch","val":"on"}', 2, False)
                                            self.mqttc.publish(
                                                "plugwise2py/cmd/switch/" +
                                                circle.mac,
                                                '{"mac":"","cmd":"switch","val":"off"}',
                                                2,
                                                False)

                                else:
                                    print(
                                            "Circle %s von Maschine %s ist jetzt %s" %
                                            (circle.mac, machine.name, data["switch"]))
                                    circle.status = data["switch"]
                                    circle.save()
                                    Group('users').send({
                                        'text': json.dumps({
                                            'type': 'circle',
                                            'circle': circle.id,
                                            'machine': machine.id,
                                            'switch': data["switch"],
                                        })
                                    })

                    elif str(topic[1]) == "cmd":
                        # print ("Kommando empfangen!\n" + msg.topic + "\n" + msg.payload.decode('UTF-8') + "\n\n")
                        pass
        except Exception as e:
            print(e)

    def login(self, esp_mac, data):
        from channels import Group
        from .models import FabLabUser, ESP, UserActivityMonitor
        import json
        import datetime

        esp = None
        machine = None
        try:
            esp = ESP.objects.get(mac=esp_mac)
            machine = esp.machine
        except Exception as e:
            fehlertext = u"Fehlerhafter Anmeldeversuch, ESP oder Maschine nicht gefunden! esp_mac : %s data : %s Fehler : %s" % (
                esp_mac, data, e)
            print(fehlertext)
            Group('users').send({
                'text': json.dumps({
                    'type': 'error',
                    'text': fehlertext
                })
            })
            if machine:
                for esp in machine.esps.all():
                    self.mqttc.publish("FabLab/" + esp.mac + "/status", "{\"cmd\":\"0\"}", 2, True)

        fablabuser = None
        try:
            fablabuser = FabLabUser.objects.get(rfid_uuid=data["data"])
        except Exception as e:
            fehlertext = u"Fehlerhafter Anmeldeversuch, Benutzer nicht gefunden! esp_mac : %s data : %s Fehler : %s" % (
                esp_mac, data, e)
            print(fehlertext)
            Group('users').send({
                'text': json.dumps({
                    'type': 'error',
                    'text': fehlertext
                })
            })
            if machine:
                for esp in machine.esps.all():
                    self.mqttc.publish("FabLab/" + esp.mac + "/status", "{\"cmd\":\"0\"}", 2, True)

        # anmelden wenn maschine und user gefunden, user hat rechte und die maschine ist Idle
        if machine and fablabuser:
            if fablabuser in machine.users.all() and not machine.user:
                # print ("Benutzer %s %s an Maschine %s angemeldet, bestätige Login...") % (fablabuser.user.first_name,  fablabuser.user.last_name, machine.name)
                machine.user = fablabuser
                machine.save()

                # teste ob benutzer in monitor gruppe
                if fablabuser.user.groups.filter(name='UserActivityGroup').exists():
                    activity = UserActivityMonitor(
                        datestart=datetime.datetime.now(),
                        user=fablabuser,
                        machine=machine)
                    activity.save()

                for esp in machine.esps.all():
                    self.mqttc.publish("FabLab/" + esp.mac + "/status", "{\"cmd\":\"2\"}", 2, True)
                for circle in machine.circles.all():
                    self.mqttc.publish(
                        "plugwise2py/cmd/switch/" +
                        circle.mac,
                        '{"mac":"","cmd":"switch","val":"on"}',
                        2,
                        False)

                Group('users').send({
                    'text': json.dumps({
                        'type': 'machine',
                        'machine': machine.id,
                        'user': u'%s&nbsp;%s' % (fablabuser.user.first_name, fablabuser.user.last_name),
                    })
                })
            else:
                fehlertext = u"Fehlerhafter Anmeldeversuch an Maschine %s Benutzer : %s %s" % (
                    machine.name, fablabuser.user.first_name, fablabuser.user.last_name)
                print(fehlertext)
                Group('users').send({
                    'text': json.dumps({
                        'type': 'error',
                        'text': fehlertext
                    })
                })
                for esp in machine.esps.all():
                    self.mqttc.publish("FabLab/" + esp_mac + "/status", "{\"cmd\":\"0\"}", 2, True)

    def logout(self, esp_mac, data):
        from channels import Group
        from .models import ESP, UserActivityMonitor
        import json
        import datetime

        esp = None
        machine = None
        # Machine.objects.select_for_update().get(esp_mac=esp_mac)
        try:
            esp = ESP.objects.get(mac=esp_mac)
            machine = esp.machine
        except Exception as e:
            fehlertext = u"Fehlerhafter Abmeldeversuch, ESP oder Maschine nicht gefunden! esp_mac : %s data : %s Fehler : %s" % (
                esp_mac, data, e)
            print(fehlertext)
            Group('users').send({
                'text': json.dumps({
                    'type': 'error',
                    'text': fehlertext
                })
            })
            if machine:
                for esp in machine.esps.all():
                    self.mqttc.publish("FabLab/" + esp.mac + "/status", "{\"cmd\":\"2\"}", 2, True)
        else:
            # wenn benutzer angemeldet ist darf er auch abmelden
            if machine.user:
                if "data" in data and machine.user and machine.user.rfid_uuid == data["data"]:
                    # print ("TAG " + data["data"]  + " an Maschine " + machine.name + " abgemeldet, bestaetige Logout...")

                    if machine.user.user.groups.filter(name='UserActivityGroup').exists():
                        activity = UserActivityMonitor.objects.filter(
                            user__in=[machine.user], machine__in=[machine]).latest('datestart')
                        if activity.datestop is None:
                            activity.datestop = datetime.datetime.now()
                            activity.save()

                    machine.user = None
                    machine.save()

                    for esp in machine.esps.all():
                        self.mqttc.publish(
                            "FabLab/" +
                            esp.mac +
                            "/status",
                            "{\"cmd\":\"0\"}",
                            2,
                            True)
                    for circle in machine.circles.all():
                        self.mqttc.publish("plugwise2py/cmd/switch/" + circle.mac,
                                      '{"mac":"","cmd":"switch","val":"off"}', 2, False)

                    Group('users').send({
                        'text': json.dumps({
                            'type': 'machine',
                            'machine': machine.id,
                            'user': 'None',
                        })
                    })
                else:
                    for esp in machine.esps.all():
                        self.mqttc.publish(
                            "FabLab/" +
                            esp.mac +
                            "/status",
                            "{\"cmd\":\"2\"}",
                            2,
                            True)

                    fehlertext = u"Fehlerhafter Abmeldeversuch an Maschine %s!" % (
                        machine.name)
                    print(fehlertext)
                    Group('users').send({
                        'text': json.dumps({
                            'type': 'error',
                            'text': fehlertext
                        })
                    })
            else:
                for esp in machine.esps.all():
                    self.mqttc.publish("FabLab/" + esp.mac + "/status", "{\"cmd\":\"0\"}", 2, True)

                fehlertext = u"Fehlerhafter Abmeldeversuch an Maschine %s! Kein Benutzer angemeldet...." % (
                    machine.name)
                print(fehlertext)
                Group('users').send({
                    'text': json.dumps({
                        'type': 'error',
                        'text': fehlertext
                    })
                })

    # callback funktion um signale von webseite zu empfangen
    # in consumers.py werden die websocket funktionen definiert,
    # von dort wird das signal gesendet
    def signal_callback(self, sender, **kwargs):
        from .models import Machine, FabLabUser, UserActivityMonitor, PlugwiseCircle
        from channels import Group
        import simplejson as json
        import datetime

        #print ("mqtt script hat signal empfangen..." + sender)
        # print (kwargs['message'])

        data = json.loads(kwargs['message'])

        if 'cmd' in data and data['cmd'] == 'save':

            # hinzufügen und entfernen -> conf -> pw2py neu starten
            # einstellungen -> control
            circle = PlugwiseCircle.objects.get(pk=data["circle"])

            with open("{0}/config/{1}".format(PLUGWISE_2_PY, "pw-conf.json")) as f:
                pw_conf = json.load(f)

            with open("{0}/config/{1}".format(PLUGWISE_2_PY, "pw-control.json")) as f:
                pw_control = json.load(f)

            #print(pw_conf)
            #print(pw_control)

            #"mac": "000D6F0003973B9D",
            #  "category": "IT",
            #  "name": "circle+",
            #  "loginterval": "15",
            #  "always_on": "False",
            #  "production": "False",
            #  "location": "FabLab"

            gefunden = False
            for c in pw_conf["static"]:
                if c["mac"] == circle.mac:
                    gefunden = True
                    print("Circle gefunden, Statische pw2py config muss nicht geändert werden!")
            if not gefunden:
                print("Circle nicht gefunden, Statische pw2py config muss angepasst werden!")

            # "switch_state": "on",
            # "name": "circle+",
            # "schedule_state": "off",
            # "schedule": "",
            # "mac": "000D6F0003973B9D",
            # "savelog": "yes",
            # "monitor": "no"

            else:
                for c in pw_control["dynamic"]:
                    if c["mac"] == circle.mac:

                        if not ((c["monitor"] == 'yes' and circle.monitor) or (c["monitor"] == 'no' and not circle.monitor )):
                            print("Monitor geändert {} - {}".format(c["monitor"],circle.monitor))

                        if not ((c["savelog"] == 'yes' and circle.savelog) or (c["savelog"] == 'no' and not circle.savelog)):
                            print("Savelog geändert {} - {}".format(c["savelog"], circle.savelog))


        elif 'cmd' in data and data['cmd'] == 'switch':
            machine = None
            try:
                machine = Machine.objects.get(id=data["data"])
            except Exception as e:
                fehlertext = u"Machine nicht im System gefunden! data : %s Fehler : %s" % (
                    data, e)
                print(fehlertext)
                Group('users').send({
                    'text': json.dumps({
                        'type': 'error',
                        'text': fehlertext
                    })
                })

            webuser = None
            try:
                webuser = FabLabUser.objects.get(id=data["user"])
            except Exception as e:
                fehlertext = u"Benutzer nicht im System gefunden! data : %s Fehler : %s" % (
                    data, e)
                print(fehlertext)
                Group('users').send({
                    'text': json.dumps({
                        'type': 'error',
                        'text': fehlertext
                    })
                })

            if machine and webuser and webuser.user.is_superuser:
                if not machine.user:
                    # machine.esp_status = 'Manual'
                    machine.user = webuser
                    machine.save()

                    # teste ob benutzer in monitor gruppe
                    try:
                        if webuser.user.groups.filter(name='UserActivityGroup').exists():
                            activity = UserActivityMonitor(
                                datestart=datetime.datetime.now(), user=webuser, machine=machine)
                            activity.save()
                    except:
                        pass

                    for circle in machine.circles.all():
                        self.mqttc.publish("plugwise2py/cmd/switch/" + circle.mac,
                                      '{"mac":"","cmd":"switch","val":"on"}', 2, False)

                    for esp in machine.esps.all():
                        self.mqttc.publish(
                            "FabLab/" +
                            esp.mac +
                            "/status",
                            "{\"cmd\":\"2\"}",
                            2,
                            True)

                    fehlertext = u"Schalte Machine %s manuell an!" % machine.name
                    print(fehlertext)
                    Group('users').send({
                        'text': json.dumps({
                            'type': 'error',
                            'text': fehlertext
                        })
                    })
                    Group('users').send({
                        'text': json.dumps({
                            'type': 'machine',
                            'machine': machine.id,
                            'user': u'%s&nbsp;%s' % (webuser.user.first_name, webuser.user.last_name),
                        })
                    })
                else:
                    # teste ob benutzer in monitor gruppe

                    try:
                        if machine.user.user.groups.filter(name='UserActivityGroup').exists():
                            activity = UserActivityMonitor.objects.filter(
                                user__in=[machine.user], machine__in=[machine]).latest('datestart')
                            if activity and not activity.datestop:
                                activity.datestop = datetime.datetime.now()
                                activity.save()
                    except:
                        pass

                    machine.user = None
                    machine.save()

                    # esp abmelden
                    for esp in machine.esps.all():
                        self.mqttc.publish(
                            "FabLab/" +
                            esp.mac +
                            "/status",
                            "{\"cmd\":\"0\"}",
                            2,
                            True)

                    for circle in machine.circles.all():
                        self.mqttc.publish("plugwise2py/cmd/switch/" + circle.mac,
                                      '{"mac":"","cmd":"switch","val":"off"}', 2, False)

                    fehlertext = u"Schalte Machine %s manuell aus!" % machine.name
                    print(fehlertext)
                    Group('users').send({
                        'text': json.dumps({
                            'type': 'error',
                            'text': fehlertext
                        })
                    })
                    Group('users').send({
                        'text': json.dumps({
                            'type': 'machine',
                            'machine': machine.id,
                            'user': 'None',
                        })
                    })
