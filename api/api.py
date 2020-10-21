import threading
import time
import logging

from flask import Flask, jsonify, request
from humanfriendly import format_timespan
from pi import PiDisplay, PiGPIO


logging.getLogger(__name__)


app = Flask(__name__)
app.config["SECRET_KEY"] = 'shedapi'
lightsOn = False
fanTimer = 0
pause = 0
PiD = PiDisplay()
PiIO = PiGPIO()


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
    global fanTimer
    global lightsOn
    data = standardData()
    if val > 0:
        if obj == "fan":
            switchFan(True, t=val)
            message = "{} added to the fan timer.".format(format_timespan(int(val)))
            logging.info(message)
            data.update({
                "fanTimer": fanTimer,
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
        global lightsOn
        s = int(not lightsOn)
    if obj == "fan":
        logging.info("Switching fan.")
        global fanTimer
        logging.info("fanTimer Value: {}".format(fanTimer))
        if fanTimer > 1:
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
        global lightsOn
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
    global pause
    data = standardData()
    if (type(sleep) != int):
        data.update({
            "success": False,
            "message": "Sleep time not an integer."
        })
        return jsonify(data)
    else:
        pause = (sleep + 1)
        while pause > 0:
            info = PiD.showStats()
            time.sleep(0.5)
    data["message"] = "Finished displaying data."
    for k in info.keys():
        data["debugmessage"] = (data["debugmessage"] + " " + info[k])
    return jsonify(data)


@app.route('/stats/vars', methods=['GET'])
def apiShowVars():
    # Shows the value of the standard variables on the screen for 5 seconds.
    logging.info("Request URL: {} | User Agent: {} | Host: {}".format(request.url,
                                                                      request.user_agent,
                                                                      request.host))
    logging.info("api.apiShowVars Function")
    global PiD
    global pause
    pause = 10
    while pause > 0:
        data = standardData()
        del data["message"]
        del data["success"]
        # del data["pause"]
        data["pin4"] = PiIO.readPin(4)
        data["pin17"] = PiIO.readPin(17)
        logging.info("apiShowVars Var Data: {}".format(data))
        PiD.showVars(data)
        time.sleep(1)
    data["debugmessage"] = str(data)
    data.update(standardData())
    data.update({
        "success": True,
        "message": "Finished displaying data."
    })
    return jsonify(data)


@app.route('/stats/pins', methods=['GET'])
def apiShowPins():
    # Shows the value of the standard variables on the screen for 5 seconds.
    logging.info("Request URL: {} | User Agent: {} | Host: {}".format(request.url,
                                                                      request.user_agent,
                                                                      request.host))
    logging.info("api.apiShowPins Function")
    global PiD
    global pause
    pause = 10
    while pause > 0:
        pdata = {
            "pin17": PiIO.readPin(17),
            "pin22": PiIO.readPin(22),
            "pin23": PiIO.readPin(23),
            "pin24": PiIO.readPin(24)
        }
        logging.info("apiShowPins Var Data: {}".format(pdata))
        PiD.showVars(pdata)
        time.sleep(0.3)
    data = standardData()
    data.update({
        "success": True,
        "message": "Finished displaying data.",
        "pdata": pdata
    })
    return jsonify(data)


# Non-route functions


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
    global lightsOn
    global fanTimer
    global PiIO
    global pause
    data = {
        "fanTimer": fanTimer,
        "lights": lightsOn,
        "success": True,
        "message": "",
        "debugmessage": "",
        "piconnected": PiIO.pi.connected,
        "pause": pause
    }
    logging.info("standardData returned: {}".format(str(data)))
    return data


def switchFan(s, t=900):
    # Adds and removes time from the fan timer, and actually switches the
    # physical object on and off accordingly. 's' is a boolean value, 't'
    # is only used if 's' is True.
    global fanTimer
    logging.info("api.switchFan Function: s: {}, t:{}".format(s, t))
    if not s:
        fanTimer = 0
        PiD.writeFanTimer(0)
    else:
        fanTimer = fanTimer + t
    logging.info("api.switchFan about to run PiIO.switchFan with argument s: {}".format(int(s)))
    PiIO.switchFan(int(s))


def switchLights(s):
    # Physically switches the lights on and off.
    logging.info("api.switchLights Function: s: {}".format(s))
    global lightsOn
    lightsOn = s
    PiIO.switchLight(int(s))


def checker():
    # The background function that keeps track of the fan timer
    # and writes its value to the screen.
    global lightsOn
    global fanTimer
    global PiD
    global pause
    sleep_c = 0
    while True:
        if pause > 0:
            pause -= 1
            if pause < 0:
                pause = 0
        else:
            if fanTimer > 0:
                PiD.writeFanTimer(fanTimer)
                sleep_c = 0
                fanTimer -= 1
                if fanTimer == 0:
                    logging.info("api.checker switching off the fan!")
                    switchFan(False)
            else:
                sleep_c += 1
                if sleep_c == 10:
                    PiD.screenOff()
                if fanTimer < 0:
                    fanTimer = 0
        time.sleep(1)
        # PiIO.readPin(22)


checkT = threading.Thread(group=None, target=checker)
checkT.daemon = True
checkT.start()

if __name__ == "__main__":
    app.run()
