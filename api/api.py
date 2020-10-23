import threading
import time
import logging

from flask import Flask, jsonify, request
from humanfriendly import format_timespan
from pi import PiDisplay, PiGPIO


logging.getLogger(__name__)

class APIData():
    def __init__(self):
        self.lightsOn = False
        self.fanTimer = 0
        self.pause = 0


app = Flask(__name__)
app.config["SECRET_KEY"] = 'shedapi'
APID = APIData()
PiD = PiDisplay()
PiIO = PiGPIO(APID)

# Route functions


@app.route('/', methods=['GET'])
def apiIndex():
    # Returns standard data of variable values.
    logging.info("Request URL: {} | User Agent: {} | Host: {}".format(request.url,
                                                                      request.user_agent,
                                                                      request.host))
    data = standardData()
    return jsonify(data)


@app.route('/add/<obj>/<int:val>', methods=['POST'])
def apiAdd(obj, val):
    # Adds time to the fan counter, ignores the lights.
    logging.info("Request URL: {} | User Agent: {} | Host: {}".format(request.url,
                                                                      request.user_agent,
                                                                      request.host))
    logging.info("api.apiAdd Function: obj: {}, val: {}".format(obj, val))
    global APID
    data = standardData()
    if val > 0:
        if obj == "fan":
            switchFan(True, t=val)
            message = "{} added to the fan timer.".format(format_timespan(int(val)))
            logging.info(message)
            data.update({
                "fanTimer": APID.fanTimer,
                "message": message
            })
        if obj == "lights":
            data["message"] = "Lights have no timer function."
            data["success"] = False
    else:
        data["message"] = "0s selected - nothing to do."
        data["success"] = False
    return jsonify(data)


@app.route('/switch/<obj>', methods=['POST'])
def apiSwitchDefault(obj):
    # Switches the lights or fan either on or off - whichever it wasn't previously.
    logging.info("Request URL: {} | User Agent: {} | Host: {}".format(request.url,
                                                                      request.user_agent,
                                                                      request.host))
    logging.info("api.apiSwitchDefault Function: obj: {}".format(obj))
    s = 0
    if obj == "lights":
        global APID
        s = int(not APID.lightsOn)
    if obj == "fan":
        logging.info("Switching fan.")
        logging.info("fanTimer Value: {}".format(APID.fanTimer))
        if APID.fanTimer > 1:
            logging.info("Greater than one, so switching 's' to 0.")
            s = 0
        else:
            logging.info("Less than one, so switching 's' to 900.")
            s = 900
    r = apiSwitchValue(obj, s)
    return r


@app.route('/switch/<obj>/<int:val>', methods=['POST'])
def apiSwitchValue(obj, val):
    # Switches the lights or fan either on or off, using the int 'val' as a
    # boolean for lights and a time value for fan. In both cases, a value of 0
    # switches the relevant object off.
    logging.info("Request URL: {} | User Agent: {} | Host: {}".format(request.url,
                                                                      request.user_agent,
                                                                      request.host))
    logging.info("api.apiSwitchValue Function: obj: {}, val: {}".format(obj, val))
    s = bool(val)
    if obj == "lights":
        switchLights(s)
    if obj == "fan":
        switchFan(s, val)
    data = standardData()
    data["message"] = "{} switched {}.".format(obj.title(), status(val).title())
    logging.info(data["message"])
    return jsonify(data)


@app.route('/stats', methods=['GET'])
def apiShowStatsDefault():
    # Shows some hardware stats on the screen for 10s
    logging.info("Request URL: {} | User Agent: {} | Host: {}".format(request.url,
                                                                      request.user_agent,
                                                                      request.host))
    r = apiShowStats(10)
    return r


@app.route('/stats/<int:sleep>', methods=['POST'])
def apiShowStats(sleep):
    # Shows some hardware stats on the screen for the given time.
    logging.info("Request URL: {} | User Agent: {} | Host: {}".format(request.url,
                                                                      request.user_agent,
                                                                      request.host))
    logging.info("api.apiShowStatus Function: sleep: {}".format(sleep))
    global PiD
    data = standardData()
    if (type(sleep) != int):
        data.update({
            "success": False,
            "message": "Sleep time not an integer.",
            "debugmessage": "Malformed POST request."
        })
        return jsonify(data)
    else:
        info = PiD.showStats()
        # Before we return the json data, we'll kick off a thread updating the screen.
        dispStats = threading.Thread(group=None, target=displayStats, args=(sleep,))
        dispStats.daemon = True
        dispStats.start()
    data["message"] = "Now displaying Pi hardware statistics for {}s.".format(sleep)
    for k in info.keys():
        if data["debugmessage"] == "":
            data["debugmessage"] = info[k]
        else:
            data["debugmessage"] = "{},{}".format(data["debugmessage"], info[k])
    return jsonify(data)


@app.route('/stats/vars', methods=['GET'])
def apiShowVars():
    # Shows the value of the standard variables on the screen for 5 seconds.
    logging.info("Request URL: {} | User Agent: {} | Host: {}".format(request.url,
                                                                      request.user_agent,
                                                                      request.host))
    logging.info("api.apiShowVars Function")
    global PiD
    data = standardData()
    del data["message"]
    del data["success"]
    # del data["pause"]
    data["pin4"] = PiIO.readPin(22)
    data["pin17"] = PiIO.readPin(17)
    logging.info("apiShowVars Var Data: {}".format(data))
    PiD.showVars(data)
    data["debugmessage"] = str(data)
    data.update({
        "success": True,
        "message": "Finished displaying data."
    })
    # Before we return the json data, we'll kick off a thread updating the screen.
    dispVars = threading.Thread(group=None, target=displayVars, args=(10,))
    dispVars.daemon = True
    dispVars.start()
    return jsonify(data)


@app.route('/stats/pins', methods=['GET'])
def apiShowPins():
    # Shows the value of the standard variables on the screen for 5 seconds.
    logging.info("Request URL: {} | User Agent: {} | Host: {}".format(request.url,
                                                                      request.user_agent,
                                                                      request.host))
    logging.info("api.apiShowPins Function")
    global PiD
    pdata = {
        "pin17": PiIO.readPin(17),
        "pin22": PiIO.readPin(22),
        "pin23": PiIO.readPin(23),
        "pin24": PiIO.readPin(24),
        "pin18": PiIO.readPin(18)
    }
    data = standardData()
    data.update({
        "success": True,
        "message": "Finished displaying data.",
        "debugmessage": pdata
    })
    # Before we return the json data, we'll kick off a thread updating the screen.
    dispPins = threading.Thread(group=None, target=displayPins, args=(10,))
    dispPins.daemon = True
    dispPins.start()
    return jsonify(data)


# Non-route functions

def displayPins(pause_s):
    global APID
    global PiD
    APID.pause = pause_s
    while APID.pause > 0:
        pdata = {
            "pin17": PiIO.readPin(17),
            "pin22": PiIO.readPin(22),
            "pin23": PiIO.readPin(23),
            "pin24": PiIO.readPin(24)
        }
        # logging.info("apiShowPins Var Data: {}".format(pdata))
        PiD.showVars(pdata)
        time.sleep(0.3)
    PiD.byeBye()


def displayVars(pause_s):
    global APID
    global PiD
    APID.pause = pause_s
    while APID.pause > 0:
        data = standardData()
        del data["message"]
        del data["success"]
        # del data["pause"]
        data["pin22"] = PiIO.readPin(22)
        data["pin17"] = PiIO.readPin(17)
        logging.info("apiShowVars Var Data: {}".format(data))
        PiD.showVars(data)
        time.sleep(0.5)
    PiD.byeBye()


def displayStats(pause_s):
    global APID
    global PiD
    APID.pause = pause_s
    while APID.pause > 0:
        PiD.showStats()
        time.sleep(0.5)
    PiD.byeBye()


def status(s):
    # Converts various data values into 'On' or 'Off' strings, for message formatting.
    y = [1, "1", True, "true", "on"]
    n = [0, "0", False, "false", "off"]
    if type(s) == str:
        s = s.lower()
    if type(s) == int:
        if s > 0:
            s = True
        else:
            s = False
    logging.info("api.status Function: s: {}".format(s))
    if s in y:
        return "On"
    if s in n:
        return "Off"
    return "Unknown"


def standardData():
    # Returns a dict of the standard variables to return to users via JSONify
    global APID
    global PiIO
    data = {
        "fanTimer": APID.fanTimer,
        "lights": APID.lightsOn,
        "success": True,
        "message": "",
        "debugmessage": "",
        "pause": APID.pause
    }
    logging.info("standardData returned: {}".format(str(data)))
    return data


def switchFan(s, t=900):
    # Adds and removes time from the fan timer, and actually switches the
    # physical object on and off accordingly. 's' is a boolean value, 't'
    # is only used if 's' is True.
    global APID
    logging.info("api.switchFan Function: s: {}, t:{}".format(s, t))
    if not s:
        APID.fanTimer = 0
        PiD.writeFanTimer(0)
    else:
        APID.fanTimer = APID.fanTimer + t
    logging.info("api.switchFan about to run PiIO.switchFan with argument s: {}".format(int(s)))
    PiIO.switchFan(int(s))


def switchLights(s):
    # Physically switches the lights on and off.
    logging.info("api.switchLights Function: s: {}".format(s))
    global APID
    APID.lightsOn = s
    PiIO.switchLight(int(s))


def checker():
    # The background function that keeps track of the fan timer
    # and writes its value to the screen.
    global APID
    global PiD
    sleep_c = 0
    while True:
        if APID.pause > 0:
            APID.pause -= 1
            if APID.pause < 0:
                APID.pause = 0
        else:
            if not APID.fanTimer == 0:
                if APID.fanTimer < 0:
                    APID.fanTimer = 0
                else:
                    PiD.writeFanTimer(APID.fanTimer)
                    sleep_c = 0
                    APID.fanTimer -= 1
                    if APID.fanTimer == 0:
                        logging.info("api.checker switching off the fan!")
                        switchFan(False)
            else:
                sleep_c += 1
                if sleep_c == 10:
                    PiD.screenOff()
                if APID.fanTimer < 0:
                    APID.fanTimer = 0
        time.sleep(1)
        # PiIO.readPin(22)


checkT = threading.Thread(group=None, target=checker)
checkT.daemon = True
checkT.start()

if __name__ == "__main__":
    app.run()
