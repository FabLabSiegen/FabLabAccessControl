from channels.routing import route
from fablabcontrol.consumers import ws_connect, ws_disconnect, ws_receive

# channel routing, die ws_ funktionen sind in fablabcontrol.consumers.py definiert
channel_routing = [
    route('websocket.connect', ws_connect),
    route('websocket.disconnect', ws_disconnect),
    route('websocket.receive', ws_receive),
]
