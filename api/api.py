import threading
import time

from flask import Flask, jsonify
from humanfriendly import format_timespan

app = Flask(__name__)
app.config["SECRET_KEY"] = 'shedapi'
# app.config.from_object('shed.config.conf')
lightsOn = False
fanTimer = 0
# format_timespan(fanTimer)


@app.route('/', methods=['GET'])
def apiIndex():
    data = {
        "fanTimer": fanTimer,
        "lights": getLightStatus()
    }
    return jsonify(data)


@app.route('/add/<obj>/<val>', methods=['POST'])
def apiAdd(obj, val):
    if obj == "fan":
        global fanTimer
        fanTimer = fanTimer + int(val)
        message = "{} added to the fan timer.".format(format_timespan(int(val)))
    data = {
        "fanTimer": fanTimer,
        "lights": getLightStatus(),
        "success": True,
        "message": message
    }
    return jsonify(data)


@app.route('/switch/<obj>/<val>', methods=['POST'])
def apiSwitch(obj, val):
    if obj == "lights":
        switchLights(val)
    if obj == "fan":
        switchFan(val)
    message = "{} switched {}.".format(obj.title(), val.title())
    data = {
        "fanTimer": fanTimer,
        "lights": getLightStatus(),
        "success": True,
        "message": message
    }
    return jsonify(data)


def switchLights(val):
    global lightsOn
    if val == "On":
        lightsOn = True
    if val == "Off":
        lightsOn = False


def switchFan(val):
    global fanTimer
    fanTimer = 0


def checker():
    global lightsOn
    global fanTimer
    while True:
        if fanTimer > 0:
            fanTimer -= 1
            if fanTimer == 0:
                switchFan(False)
        time.sleep(1)


def getLightStatus():
    global lightsOn
    if lightsOn:
        return "On"
    else:
        return "Off"


checkT = threading.Thread(group=None, target=checker)
checkT.daemon = True
checkT.start()

if __name__ == "__main__":
    app.run()
