import pigpio
import time

pi = pigpio.pi(host='pi3.local')
print(pi.connected)
pin = 4
pi.set_mode(pin, pigpio.OUTPUT)
while True:
    print("On!")
    pi.write(pin, 1)
    time.sleep(1)
    print("Off!")
    pi.write(pin, 0)
    time.sleep(1)


# from gpiozero import LED
# import time

# red = LED(4)

# while True:
#     red.on()
#     time.sleep(1)
#     red.off()
#     time.sleep(1)