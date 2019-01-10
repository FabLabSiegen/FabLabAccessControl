default_app_config = 'fablabcontrol.apps.FabLabControl'

# starten des mqtt client, loop_start startet als hintergrund thread
# from . import mqtt
# mqtt.mqttc.loop_start()
# mqtt.opendash_mqttc.loop_start()

from .fablabcontrol import fablabcontrolThread
import threading

#madsensors.XBEE = madsensors.xbee_start()
stop_thread = threading.Event()
fab_thread = fablabcontrolThread(stop_thread)
fab_thread.start()