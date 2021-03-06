import os
import sys
import time
import threading
import subprocess
import logging
import time

import board
import busio
import adafruit_ssd1306 as af
# import pigpio
import RPi.GPIO as GPIO
from PIL import Image, ImageDraw, ImageFont

logging.getLogger(__name__)


class PiGPIO():
    def __init__(self, APID):
        GPIO.cleanup()
        self.PiD = PiDisplay()
        self.fan_p = 22
        self.light_p = 17
        self.buttonA_p = 18
        self.buttonB_p = 23
        self.buttonC_p = 24
        self.error_p = 4
        self.usedPins = [22, 23, 24, 17, 18, 4]
        self.APID = APID
        # self.pi = pigpio.pi(host='localhost')
        self.pi = GPIO
        self.pi.setmode(GPIO.BCM)
        self.pi.setup(self.light_p, GPIO.OUT, initial=GPIO.LOW)
        self.pi.setup(self.fan_p, GPIO.OUT, initial=GPIO.LOW)
        self.pi.setup(self.error_p, GPIO.OUT, initial=GPIO.LOW)
        self.pi.setup(self.buttonB_p, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
        self.pi.setup(self.buttonA_p, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
        self.pi.setup(self.buttonC_p, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
        self.pi.add_event_detect(self.buttonA_p,
                                 GPIO.RISING,
                                 callback=self.broadcastFlickLights,
                                 bouncetime=700)
        self.pi.add_event_detect(self.buttonB_p,
                                 GPIO.RISING,
                                 callback=self.broadcastAddFanTime,
                                 bouncetime=600)
        self.pi.add_event_detect(self.buttonC_p,
                                 GPIO.RISING,
                                 callback=self.broadcastFanOff,
                                 bouncetime=200)

    def broadcastFlickLights(self, pin):
        time.sleep(0.05)
        if self.pi.input(self.buttonA_p) == 1:
            logging.info("broadcastA Triggered!")
            if self.APID.lightsOn is True:
                msg = "Lights: Off"
                self.PiD.writeText(msg)
                self.pi.output(self.light_p, 0)
                self.APID.lightsOn = False
            else:
                msg = "Lights: On"
                self.PiD.writeText(msg)
                self.pi.output(self.light_p, 1)
                self.APID.lightsOn = True
            self.APID.pause = 3
            self.APID.sleep_c = 0
        else:
            logging.info("False positive on A")
            self.pi.output(self.error_p, 1)
            time.sleep(0.1)
            self.pi.output(self.error_p, 0)

    def broadcastAddFanTime(self, pin):
        time.sleep(0.05)
        if self.pi.input(self.buttonB_p) == 1:
            logging.info("broadcastB Triggered!")
            # self.PiD.writeText("Fan Timer:\n+30m")
            self.APID.fanTimer = self.APID.fanTimer + 1800
            self.switchFan(self.APID.fanTimer)
            self.PiD.writeFanTimer(self.APID.fanTimer, msg="+30m")
            self.APID.pause = 1
        else:
            logging.info("False positive on B")
            self.pi.output(self.error_p, 1)
            time.sleep(0.1)
            self.pi.output(self.error_p, 0)

    def broadcastFanOff(self, pin):
        time.sleep(0.05)
        if self.pi.input(self.buttonC_p) == 1:
            logging.info("broadcastC Triggered!")
            # self.pi.output(self.fan_p, 0)
            self.APID.fanTimer = 0
            self.switchFan(self.APID.fanTimer)
            self.PiD.writeFanTimer(self.APID.fanTimer)
            # time.sleep(3)
            # self.PiD.byeBye()
        else:
            logging.info("False positive on B")
            self.pi.output(self.error_p, 1)
            time.sleep(0.1)
            self.pi.output(self.error_p, 0)

    def switchFan(self, s):
        logging.info("pi.switchFan run from {}".format(sys._getframe().f_back.f_code.co_name))
        s = int(s)
        logging.info("Setting {} for pin {}".format(s, self.fan_p))
        self.pi.output(self.fan_p, int(s))

    def switchLight(self, s):
        logging.info("pi.switchLight run from {}".format(sys._getframe().f_back.f_code.co_name))
        s = int(s)
        logging.info("Setting {} for pin {}".format(s, self.light_p))
        self.pi.output(self.light_p, int(s))

    def readPin(self, p):
        logging.info("pi.readPin run from {}".format(sys._getframe().f_back.f_code.co_name))
        p_v = self.pi.input(p)
        logging.info("Pin {} is set to {}".format(p, p_v))
        return p_v

    def writePin(self, p, state):
        logging.info("pi.writePin run from {}".format(sys._getframe().f_back.f_code.co_name))
        try:
            p = int(p)
            state = bool(state)
        except TypeError:
            return False
        if p not in self.usedPins:
            self.pi.setup(p, GPIO.OUT, initial=state)
            self.usedPins.insert(0, p)
        else:
            self.pi.output(p, state)
        return "Pin {} set to {}".format(p, state)


class PiDisplay():
    def __init__(self):
        i2c = busio.I2C(board.SCL, board.SDA)
        self.oled = af.SSD1306_I2C(128, 64, i2c)
        self.oled.fill(0)
        self.oled.show()
        self.pad = 2
        self.top = self.pad
        self.left = self.pad
        self.right = self.oled.width - self.pad
        self.bottom = self.oled.height - self.pad
        self.image = Image.new("1", (self.oled.width, self.oled.height), color=0)
        draw = ImageDraw.Draw(self.image)
        basedir = os.path.abspath(os.path.dirname(__file__))
        rob = os.path.join(basedir, "Fonts", "RobotoMono-ExtraLight.ttf")
        opensans = os.path.join(basedir, "Fonts", "OpenSans-Bold.ttf")
        try:
            self.font = ImageFont.truetype(opensans, 22)
            self.font_sml = ImageFont.truetype(rob, 12)
            logging.info("Successfully loaded RobotoMono-ExtraLight and OpenSans-Bold Font.")
        except OSError:
            logging.info(
                "Error loading RobotoMono-ExtraLight or OpenSans-Bold: "
                "Falling back to load_default()")
            self.font = ImageFont.load_default()
        draw.multiline_text((self.top, self.left), "Hey Fucko!", font=self.font, fill=255)
        # Display image
        self.oled.image(self.image)
        self.oled.show()

    def newScreen(self, color=0):
        # logging.info("newScreen run from {}".format(sys._getframe().f_back.f_code.co_name))
        image = Image.new("1", (self.oled.width, self.oled.height), color=color)
        scr = {"image": image,
               "draw": ImageDraw.Draw(image)
               }
        return scr

    def writeText(self, t, f_size="medium"):
        if f_size == "medium":
            font = self.font
        if f_size == "small":
            font = self.font_sml
        scr = self.newScreen()
        scr["draw"].multiline_text((self.left, self.top), t, font=font, fill=255)
        self.oled.image(scr["image"])
        self.oled.show()

    def writeFanTimer(self, t, msg="Fan Timer:"):
        # Expects the time in seconds as an int.
        t = int(t)
        h, r = divmod(t, 3600)
        m, s = divmod(r, 60)
        scr = self.newScreen()
        d = scr["draw"]
        message = "{}\n{}h {}m {}s".format(msg, h, m, s)
        d.multiline_text((2, 2), message, font=self.font, fill=255, align="center")
        self.oled.image(scr["image"])
        self.oled.show()

    def byeBye(self):
        scr = self.newScreen()
        self.writeText("Buh-Bye!!")
        time.sleep(3)
        self.oled.image(scr["image"])
        self.oled.show()

    def screenOff(self, quick=False):
        if not quick:
            bye = threading.Thread(group=None, target=self.byeBye)
            bye.daemon = True
            bye.start()
        else:
            scr = self.newScreen()
            self.oled.image(scr["image"])
            self.oled.show()

    def showVars(self, vs={}):
        if type(vs) is dict:
            scr = self.newScreen()
            draw = scr["draw"]
            image = scr["image"]
            lh = 0
            for k in vs.keys():
                msg = "{}: {}".format(k, str(vs[k]))
                draw.text((self.left, self.top + lh), msg, font=self.font_sml, fill=255)
                lh += 12
            self.oled.image(image)
            self.oled.show()

    def showStats(self):
        # CMD code from official CircuitPython github:
        # https://github.com/adafruit/Adafruit_CircuitPython_SSD1306/blob/master/examples/ssd1306_stats.py
        scr = self.newScreen()
        draw = scr["draw"]
        image = scr["image"]
        cmd = "hostname -I | cut -d' ' -f1"
        IP = subprocess.check_output(cmd, shell=True).decode("utf-8")
        cmd = "top -bn1 | grep load | awk '{printf \"CPU Load:%.0f%%\", $(NF-2)*100}'"
        CPU = subprocess.check_output(cmd, shell=True).decode("utf-8")
        cmd = "free -m | awk 'NR==2{printf \"Mem:%s/%s MB %.2f%%\", $3,$2,$3*100/$2 }'"
        MemUsage = subprocess.check_output(cmd, shell=True).decode("utf-8")
        cmd = 'df -h | awk \'$NF=="/"{printf "Disk:%d/%d GB  %s", $3,$2,$5}\''
        Disk = subprocess.check_output(cmd, shell=True).decode("utf-8")
        info = {
            "CPU": CPU,
            "IP": ("IP: " + IP),
            "MemUsage": MemUsage,
            "Disk": Disk
        }
        # Write four lines of text.
        draw.text((self.left, self.top + 0), "IP: " + IP, font=self.font_sml, fill=255)
        draw.text((self.left, self.top + 12), CPU, font=self.font_sml, fill=255)
        draw.text((self.left, self.top + 24), MemUsage, font=self.font_sml, fill=255)
        draw.text((self.left, self.top + 36), Disk, font=self.font_sml, fill=255)
        self.oled.image(image)
        self.oled.show()
        return info
