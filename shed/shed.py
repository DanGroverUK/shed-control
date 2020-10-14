import logging
import sys
import json

import requests as reqs
from flask import Flask, render_template, request, url_for
from humanfriendly import format_timespan

import forms

logging.basicConfig(stream=sys.stderr)
app = Flask(__name__)
try:
    basedir = path.abspath(path.dirname(__file__))
    cf = (path.join(basedir, 'config.json'))
    with open(cf, "r") as read_config:
        config = json.load(read_config)
except:
    config = {
        "name": "pi3",
        "port": 80,
        "local": True,
        "key": "8c47d75f-79e8-4dc5-aafe-091931cc15c2",
        "api": "/api",
        "server": "http://localhost"
    }
logging.error(str(config))
app.config["SECRET_KEY"] = config["key"]

URL = "{server}:{port}{api}/".format(
    server=config["server"],
    port=config["port"],
    api=config["api"])


@app.route('/', methods=['GET', 'POST'])
def index():
    FanForm = forms.FanForm()
    d = {
        "message": "",
        "fanTimer": 0,
        "lights": "Off"
    }
    # If GET
    if request.method == "GET":
        resp = reqs.get(URL + "/").json()
        d["fanTimer"] = resp["fanTimer"]
        d["lights"] = resp["lights"]
    # If Adding Time to Fan
    if request.method == "POST":
        if FanForm.add.data:
            hours = request.form["hours"]
            mins = request.form["mins"]
            total_secs = ((int(hours) * 60) + int(mins)) * 60
            post = reqs.post("{url}/add/fan/{s}".format(
                url=URL, s=total_secs)).json()
            if post["success"] is True:
                d["message"] = post["message"]
                d["fanTimer"] = post["fanTimer"]
                d["lights"] = post["lights"]
            else:
                d["message"] = "ERROR: {}".format(post["message"])
    # If turning off Fan
    if FanForm.off.data:
        post = reqs.post("{url}/switch/fan/off".format(url=URL)).json()
        d["message"] = post["message"]
        d["fanTimer"] = post["fanTimer"]
        d["lights"] = post["lights"]
    # If refreshing page
    if FanForm.refresh.data:
        resp = reqs.get(URL + "/").json()
        d["fanTimer"] = resp["fanTimer"]
        d["lights"] = resp["lights"]

    return render_template("index.html",
                           fanTimer=format_timespan(d["fanTimer"]),
                           lights=d["lights"],
                           message=d["message"],
                           FanForm=FanForm,
                           posturl=url_for('index'))


# @ app.route('/api', methods=['GET'])
# def apiIndex():
#     data = {
#         "fanTimer": format_timespan(fanTimer),
#         "lights": getLightStatus()
#     }
#     return jsonify(data)


# @ app.route('/api/add/<obj>/<val>', methods=['POST'])
# def apiAdd(obj, val, html=False):
#     if obj == "fan":
#         global fanTimer
#         fanTimer = fanTimer + int(val)
#         message = "{} added to the fan timer.".format(format_timespan(int(val)))
#     data = {
#         "fanTimer": fanTimer,
#         "lights": getLightStatus(),
#         "success": True,
#         "message": message
#     }
#     if html:
#         return data
#     else:
#         return jsonify(data)


# @ app.route('/api/switch/<obj>/<val>', methods=['POST'])
# def apiSwitch(obj, val, html=False):
#     if obj == "lights":
#         switchLights(bool(val))
#     if obj == "fan":
#         switchFan(bool(val))
#     if bool(val) is True:
#         status = "On"
#     else:
#         status = "Off"
#     message = "{} switched {}.".format(obj, status)
#     data = {
#         "fanTimer": fanTimer,
#         "lights": getLightStatus(),
#         "success": True,
#         "message": message
#     }
#     if html:
#         return data
#     else:
#         return jsonify(data)


# def switchLights(val):
#     pass


# def switchFan(val):
#     pass


# def checker():
#     global lightsOn
#     global fanTimer
#     while True:
#         if fanTimer > 0:
#             fanTimer -= 1
#             if fanTimer == 0:
#                 switchFan(False)
#         time.sleep(1)


# def getLightStatus():
#     global lightsOn
#     if lightsOn:
#         return "On"
#     else:
#         return "Off"


# checkT = threading.Thread(group=None, target=checker)
# checkT.daemon = True
# checkT.start()

if __name__ == "__main__":
    app.run()
