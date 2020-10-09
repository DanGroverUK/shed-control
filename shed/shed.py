import threading
import time
import datetime

from flask import Flask, render_template, request, url_for, redirect
from humanfriendly import format_timespan

import forms

app = Flask(__name__)
app.config["SECRET_KEY"] = '5f352379324c22463451387a0aec5d2f'
app.config['APPLICATION_ROOT'] = '/shed'
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
        time.sleep(1)

def lightStatus():
    global lightsOn
    if lightsOn:
        return "On"
    else:
        return "Off"

@app.route('/', methods=('GET', 'POST'))
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
            add(total_secs)
        if FanForm.off.data:
            global fanTimer
            fanTimer = 0
            message = "Fan turned off!"
        if FanForm.refresh.data:
            pass
    if request.method == "GET":
        message = url_for('index')
    return render_template("index.html",
                           fanTimer=format_timespan(fanTimer),
                           lights=lightStatus(),
                           message=message,
                           FanForm=FanForm,
                           posturl=url_for('index'))

# @app.route('/add')
# def add():
#     global fanTimer
#     fanTimer = fanTimer + 60
#     return redirect(url_for('index'))

@app.route('/add/<val>')
def add(val):
    try:
        val = int(val)
        global fanTimer
        fanTimer = fanTimer + val
    except TypeError:
        print("Not an int")
    return redirect(url_for('index'))

checkT = threading.Thread(group=None, target=checker)
checkT.daemon = True
checkT.start()

if __name__ == "__main__":
    app.run()
