import dht
from machine import Pin
from time import sleep

def alternate():
    blue.toggle()
    green.toggle()
    red.toggle()
    sleep(0.2)
    
    blue.toggle()
    green.toggle()
    red.toggle()
    sleep(0.2)
    
def toggleOff():
    blue.off()
    red.off()
    green.off()


sensor = dht.DHT22(Pin(26))
blue = machine.Pin(16, machine.Pin.OUT)
red = machine.Pin(17, machine.Pin.OUT)
green = machine.Pin(18, machine.Pin.OUT)

toggleOff()
sleep(2)

sensor.measure()
temp = (sensor.temperature() * 9/5) + 32

humid = sensor.humidity()

print(temp)
alternate()

if (temp < 80):
    green.on()
else:
    red.on()