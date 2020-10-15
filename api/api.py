import threading
import time

import pigpio
from flask import Flask, jsonify
from humanfriendly import format_timespan

app = Flask(__name__)
app.config["SECRET_KEY"] = 'shedapi'
# app.config.from_object('shed.config.conf')
lightsOn = False
fanTimer = 0
pi3 = pigpio.pi(host='pi3.local')
# format_timespan(fanTimer)


def status(s):
    y = [1, "1", True, "true", "on"]
    n = [0, "0", False, "false", "off"]
    if type(s) == str:
        s = s.lower()
    if s in y:
        return "On"
    if s in n:
        return "Off"
    return "Unknown"


@app.route('/', methods=['GET'])
def apiIndex():
    global lightsOn
    data = {
        "fanTimer": fanTimer,
        "lights": lightsOn,
        "success": True,
        "message": "",
        "piconnected": pi3.connected
    }
    return jsonify(data)


@app.route('/add/<obj>/<val>', methods=['POST'])
def apiAdd(obj, val):
    global fanTimer
    global lightsOn
    if obj == "fan":
        fanTimer = fanTimer + int(val)
        apiSwitch(obj, 1)
        message = "{} added to the fan timer.".format(format_timespan(int(val)))
    data = {
        "fanTimer": fanTimer,
        "lights": lightsOn,
        "success": True,
        "message": message,
        "piconnected": pi3.connected
    }
    return jsonify(data)


@app.route('/switch/<obj>/<int:val>', methods=['POST'])
def apiSwitch(obj, val):
    val = bool(val)
    global lightsOn
    global fanTimer
    if obj == "lights":
        switchLights(val)
    if obj == "fan":
        switchFan(val)
    message = "{} switched {}.".format(obj.title(), status(val).title())
    data = {
        "fanTimer": fanTimer,
        "lights": lightsOn,
        "success": True,
        "message": message,
        "piconnected": pi3.connected
    }
    return jsonify(data)


def switchFan(val):
    global fanTimer
    # Fan is assigned to GPIO pin 4
    p = 4
    pi3.set_mode(p, pigpio.OUTPUT)
    if not val:
        fanTimer = 0
    pi3.write(p, int(val))


def switchLights(val):
    global lightsOn
    # Fan is assigned to GPIO pin 4
    p = 17
    pi3.set_mode(p, pigpio.OUTPUT)
    lightsOn = val
    pi3.write(p, int(val))


def checker():
    global lightsOn
    global fanTimer
    while True:
        if fanTimer > 0:
            fanTimer -= 1
            if fanTimer == 0:
                switchFan(False)
        time.sleep(1)


checkT = threading.Thread(group=None, target=checker)
checkT.daemon = True
checkT.start()

if __name__ == "__main__":
    app.run()
