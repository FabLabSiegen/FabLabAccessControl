# FabLabAccessControl

## Disclaimer
This project is not ready to use and still in development. There is no setup script or so. The code is just a snapshot to show how it could work. 
Search for the string "# WARNING". You need to add your credentials for MQTT broker, WIFI and database where you find this string with an applicable note.





## Key features
- Switch plugwise plugs on and off via RFID chips
- Access control via ESP8266 and RFID-reader
- Device management of plugwise devices, RFID chips and ESP8266 via webinterface
- Usermanagement via webinterface
- Communication between ESPs and backend via MQTT



## FabLabESP
Implementation for the ESPs that controls the RFID-Reader and sends MQTT commands to the broker

Paths where you have to add credentials:
FabLabESP/FabLabESP.ino

## Plugwise-2-py
Open Source project. Description copied from the readme:
Plugwise-2-py evolved in a monitoring and control server for plugwise devices.

You need to configure your plubwise devices in Plugwise-2-py/config/pw-control.json and Plugwise-2-py/config/pw-conf.json

Paths where you have to add credentials:
Plugwise-2-py/config/pw-hostconfig.json

## fablab-webif
Django-based webinterface

### Required
* Python 2 or 3
* Python-Packages:
    * Django (Version 1.11)
    * paho-mqtt
    * channels (Version <1.x)
    * simplejson
    * django_extensions
    * Pillow
    * django-bootstrap-ui
    * django-widget-tweaks
    * django-template-debug

* MQTT broker - for example mosquitto

#### Setup

Search for the string "# WARNING". You need to add your credentials for MQTT broker, WIFI and database where you find this string with an applicable note.

Paths where you have to add credentials:
fablab-webif/fablab-webif/settings.py
fablab-webif/fablab-webif/fablabcontrol.py
fablab-webif/fablab-webif/mqtt.py


1. Install Python
2. Install required python packages via `pip install packagename`. To install Django version 1.11 use the command `pip install django==1.11`

    * ```pip install django==1.11 paho-mqtt "channels<2.0\ simplejson django_extensions pillow django-bootstrap-ui django-widget-tweaks django-template-debug```

3. Install an MQTT broker
    * `pip install mosquitto`

##### Testing installation

1. Change the database in `fablab-webif/fablab-webif/settings.py` to the SQLite database
2. Setup a user with the password from the `settings.py` in the MQTT broker
    * for Mosquitto use the command `mosquitto_passwd -c /path/to/pwfile`
3. Migrate your database
    * `python2 manage.py makemigrations`
    * `python2 manage.py migrate`
4. Run server via `python manage.py runserver`

The server should now run locally.

