import threading
import time
import os
import logging

import pigpio

from flask import Flask, jsonify
from humanfriendly import format_timespan
import board
import busio
import adafruit_ssd1306 as af
# import digitalio
from PIL import Image, ImageDraw, ImageFont

basedir = os.path.abspath(os.path.dirname(__file__))
i_log = os.path.join(basedir, "logs", "api_info.log")
logging.basicConfig(filename=i_log, level=20)


class PiDisplay():
    def __init__(self):
        i2c = busio.I2C(board.SCL, board.SDA)
        self.oled = af.SSD1306_I2C(128, 64, i2c)
        self.oled.fill(0)
        self.oled.show()
        self.image = Image.new("1", (self.oled.width, self.oled.height))
        draw = ImageDraw.Draw(self.image)
        draw.rectangle((0, 0, self.oled.width, self.oled.height), outline=0, fill=0)
        draw.rectangle((5, 5, self.oled.width - 5 - 1, self.oled.height - 5 - 1),
                       outline=255,
                       fill=255)
        basedir = os.path.abspath(os.path.dirname(__file__))
        rob = os.path.join(basedir, "Roboto-Medium.ttf")
        try:
            self.font = ImageFont.truetype(rob)
            logging.info("Successfully loaded Roboto-Medium Font.")
        except OSError:
            logging.info("Error loading Roboto-Medium - falling back to load_default()")
            self.font = ImageFont.load_default()
        text = "Hey, fucko!"
        (font_width, font_height) = self.font.getsize(text)
        draw.text(
            (self.oled.width // 2 - font_width // 2, self.oled.height // 2 - font_height // 2),
            text,
            font=self.font,
            fill=0,
        )

        # Display image
        self.oled.image(self.image)
        self.oled.show()

    def writeText(self, t):
        image = Image.new("1", (self.oled.width, self.oled.height))
        draw = ImageDraw.Draw(image)
        draw.rectangle((0, 0, self.oled.width, self.oled.height), outline=0, fill=0)
        draw.rectangle((5, 5, self.oled.width - 5 - 1, self.oled.height - 5 - 1),
                       outline=255,
                       fill=255)
        (font_width, font_height) = self.font.getsize(t)
        draw.text(
            (self.oled.width // 2 - font_width // 2, self.oled.height // 2 - font_height // 2),
            t,
            font=self.font,
            fill=0,
        )
        self.oled.image(image)
        self.oled.show()

    def screenOff(self):
        image = Image.new("1", (self.oled.width, self.oled.height))
        draw = ImageDraw.Draw(image)
        draw.rectangle((0, 0, self.oled.width, self.oled.height), outline=0, fill=0)
        self.oled.image(image)
        self.oled.show()


app = Flask(__name__)
app.config["SECRET_KEY"] = 'shedapi'
lightsOn = False
fanTimer = 0
pi3 = pigpio.pi(host='pi3.local')
PiD = PiDisplay()


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
    global PiD
    sleep_c = 0
    while True:
        if fanTimer > 0:
            PiD.writeText("Fan Time: {}s".format(str(fanTimer)))
            sleep_c = 0
            fanTimer -= 1
            if fanTimer == 0:
                switchFan(False)
        else:
            sleep_c += 1
            if sleep_c == 5:
                PiD.screenOff()
        time.sleep(1)


checkT = threading.Thread(group=None, target=checker)
checkT.daemon = True
checkT.start()

if __name__ == "__main__":
    app.run()
