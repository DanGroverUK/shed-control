import threading
import time

from flask import Flask, render_template, request, url_for, redirect, jsonify
from humanfriendly import format_timespan

import forms

app = Flask(__name__)
app.config["SECRET_KEY"] = 'fishandchips'
# app.config.from_object('shed.config.conf')
lightsOn = False
fanTimer = 0

# class LightsForm(FlaskForm):
#     name = StringField('')


def checker():
    global lightsOn
    global fanTimer
    while True:
        if fanTimer > 0:
            fanTimer -= 1
            if fanTimer == 0:
                switchFan(False)
        time.sleep(1)


def lightStatus():
    global lightsOn
    if lightsOn:
        return "On"
    else:
        return "Off"


@app.route('/', methods=['GET', 'POST'])
def index():
    message = ""
    FanForm = forms.FanForm()
    if request.method == "POST":
        if FanForm.add.data:
            hours = request.form["hours"]
            mins = request.form["mins"]
            message = "Adding {} hours and {} minutes to the clock!".format(
                str(hours), str(mins))
            total_secs = ((int(hours) * 60) + int(mins)) * 60
            r = apiAdd("fan", total_secs, html=True)
            if r["success"] is True:
                message = r["message"]
            else:
                message = "ERROR: {}".format(r["message"])
        if FanForm.off.data:
            r = (apiSwitch("fan", "false")).json()
            message = r["message"]
        if FanForm.refresh.data:
            pass
    return render_template("index.html",
                           fanTimer=format_timespan(fanTimer),
                           lights=lightStatus(),
                           message=message,
                           FanForm=FanForm,
                           posturl=url_for('index'))


@app.route('/api', methods=['GET'])
def apiIndex():
    data = {
        "fanTimer": format_timespan(fanTimer),
        "lights": lightStatus()
    }
    return jsonify(data)


@app.route('/api/add/<obj>/<val>', methods=['POST'])
def apiAdd(obj, val, html=False):
    if obj == "fan":
        global fanTimer
        fanTimer = fanTimer + int(val)
        message = "{} added to the fan timer.".format(format_timespan(int(val)))
    data = {
        "fanTimer": fanTimer,
        "lights": lightStatus(),
        "success": True,
        "message": message
    }
    if html:
        return data
    else:
        return jsonify(data)


@app.route('/api/switch/<obj>/<val>', methods=['POST'])
def apiSwitch(obj, val, html=False):
    if obj == "lights":
        switchLights(bool(val))
    if obj == "fan":
        switchFan(bool(val))
    if bool(val) is True:
        status = "On"
    else:
        status = "Off"
    message = "{} switched {}.".format(obj, status)
    data = {
        "fanTimer": fanTimer,
        "lights": lightStatus(),
        "success": True,
        "message": message
    }
    if html:
        return data
    else:
        return jsonify(data)


def switchLights(val):
    pass


def switchFan(val):
    pass


checkT = threading.Thread(group=None, target=checker)
checkT.daemon = True
checkT.start()

if __name__ == "__main__":
    app.run()
