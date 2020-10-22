import logging
import sys
import json
import os

import requests as reqs
from flask import Flask, render_template, request, url_for
from humanfriendly import format_timespan

import forms

logging.basicConfig(stream=sys.stderr)
app = Flask(__name__)
config = {
    "name": "pi3",
    "port": 80,
    "local": True,
    "key": "8c47d75f-79e8-4dc5-aafe-091931cc15c2",
    "api": "/api",
    "server": "http://localhost"
}
try:
    basedir = os.path.abspath(os.path.dirname(__file__))
    cf = (os.path.join(basedir, 'config.json'))
    with open(cf, "r") as read_config:
        config = json.load(read_config)
except FileNotFoundError:
    logging.error("config.json not loaded - using defaults")
logging.error(str(config))
app.config["SECRET_KEY"] = config["key"]

URL = "{server}:{port}{api}/".format(
    server=config["server"],
    port=config["port"],
    api=config["api"])


def status(s):
    if type(s) is int:
        if s > 0:
            s = 1
    if type(s) is str:
        s = s.lower()
    y = [1, "1", True, "true", "on"]
    n = [0, "0", False, "false", "off"]
    if type(s) == str:
        s = s.lower()
    if s in y:
        return "On"
    if s in n:
        return "Off"
    return "Unknown"


@app.route('/', methods=['GET', 'POST'])
def index():
    FanForm = forms.FanForm(fhours="1", fmins="0")
    LightForm = forms.LightForm()
    DebugForm = forms.DebugForm()
    d = {
        "message": "",
        "debugmessage": "",
        "mcolor": "mwhite",
        "fanTimer": 0,
        "lights": "Off"
    }
    # If GET
    if request.method == "GET":
        resp = reqs.get(URL + "/").json()
        d["fanTimer"] = int(resp["fanTimer"])
        d["lights"] = status(resp["lights"])
    # If the form has been submittee
    if request.method == "POST":
        logging.error("Request Form data: {}".format(request.form))
        # If Adding Time to Fan
        if FanForm.fadd.data:
            hours = request.form["fhours"]
            mins = request.form["fmins"]
            total_secs = ((int(hours) * 60) + int(mins)) * 60
            post = reqs.post("{url}/add/fan/{s}".format(
                url=URL, s=total_secs)).json()
            if post["success"] is True:
                d["message"] = post["message"]
                d["fanTimer"] = int(post["fanTimer"])
                d["lights"] = status(post["lights"])
            else:
                d["message"] = "ERROR: {}".format(post["message"])
        # If turning off Fan
        if FanForm.foff.data:
            post = reqs.post("{url}/switch/fan/0".format(url=URL)).json()
            d["message"] = post["message"]
            d["fanTimer"] = int(post["fanTimer"])
            d["lights"] = status(post["lights"])
        # If refreshing page
        if FanForm.frefresh.data:
            resp = reqs.get(URL + "/").json()
            d["fanTimer"] = int(resp["fanTimer"])
            d["lights"] = status(resp["lights"])
        # If Lights are switched on
        if LightForm.lon.data:
            post = reqs.post("{url}/switch/lights/1".format(url=URL)).json()
            d["message"] = post["message"]
            d["fanTimer"] = int(post["fanTimer"])
            d["lights"] = status(post["lights"])
            d["mcolor"] = "myellow"
        # If Lights are switched on
        if LightForm.loff.data:
            post = reqs.post("{url}/switch/lights/0".format(url=URL)).json()
            d["message"] = post["message"]
            d["fanTimer"] = int(post["fanTimer"])
            d["lights"] = status(post["lights"])
            d["mcolor"] = "mblue_anim"
        # If Debug Stats are requested
        if DebugForm.dstats.data:
            resp = reqs.get(URL + "/stats").json()
            s_ls = resp["debugmessage"].split(",")
            d.update(resp)
            ns = ""
            for s in s_ls:
                if ns == "":
                    ns = s
                else:
                    ns = "{}  |  {}".format(ns, s)
            d["debugmessage"] = ns
        if DebugForm.dvars.data:
            resp = reqs.get(URL + "/stats/vars").json()
            d.update(resp)
        if DebugForm.dpins.data:
            resp = reqs.get(URL + "/stats/pins").json()
            d.update(resp)

    return render_template("index.html",
                           fanTimer=format_timespan(d["fanTimer"]),
                           lights=status(d["lights"]),
                           message=d["message"],
                           debugmessage=d["debugmessage"],
                           mcolor=d["mcolor"],
                           FanForm=FanForm,
                           LightForm=LightForm,
                           DebugForm=DebugForm,
                           posturl=url_for('index'))


if __name__ == "__main__":
    app.run()
